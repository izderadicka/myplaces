'''
Created on Jun 7, 2013

@author: ivan
'''

from django.utils.translation import ugettext as _
import tempfile
import csv
import codecs
import logging
import re
from collections import defaultdict
from myplaces.geocode import get_coordinates
from myplaces import geocode, remote
log=logging.getLogger('mp.implaces')
from models import Place, Address, PlacesGroup
from django.db import transaction

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self


def save_file(uploaded_file):
    temp_file=tempfile.NamedTemporaryFile(suffix='.upload', prefix='myplaces-', delete=False)
    with temp_file:
        for chunk in uploaded_file.chunks():
            temp_file.write(chunk)
            
    return temp_file.name

def extact_headers(csv_file, encoding='utf-8'):
    with file(csv_file, 'rb') as f:
        reader=UnicodeReader(f, encoding=encoding)
        headers=reader.next()
        length=[0 for i in range(len(headers))]
        lines=[]
        for i,l in enumerate(reader):
            if i>=5:
                break
            lines.append(l)
            for j in range(len(l)):
                if j<len(length) and len(l[j])>length[j]:
                    length[j]=len(l[j])
                if len(l[j])>77:
                    l[j]=l[j][:77]+'...'            
        
    return headers, length, lines

MAPPABLE_FIELDS=['name', 'description', 'url',
                 'address.street', 'address.city', 'address.county', 'address.state', 
                 'address.postal_code',
                 'address.country', 'address.unformatted', 'address.email', 'address.phone']
def get_mappable_fields():
#     skip_fields=Auditable._meta.get_all_field_names()  # @UndefinedVariable
#     skip_fields.extend(['id', 'group', 'position', 'address'])
#     fields=[name for name  in Place._meta.get_all_field_names() if name not in skip_fields]  # @UndefinedVariable
#     fields=map(lambda n: (n, unicode(Place._meta.get_field(n).verbose_name)), fields)  # @UndefinedVariable
    base_model=Place
    result=[]
    def fmt_name(model, field):
        max_length=unicode(model._meta.get_field(field).max_length)
        return unicode(model._meta.get_field(field).verbose_name) +u' (%s)'%max_length
    for f in MAPPABLE_FIELDS:
        if f.find('.')>=0:
            f1,f2=f.split('.')
            other_model=base_model._meta.get_field(f1).rel.to
            result.append((f, unicode(other_model._meta.verbose_name)+'.'+ 
                          fmt_name(other_model,f2)))
        else:
            result.append((f, fmt_name(base_model,f)))
            
    result.extend((('pos.x', _('Coordinates - Longitute')), 
                   ('pos.y', _('Coordinates - Latitude')),
                   ('pos.xy', _('Coordinates - Lng, Lat')),
                   ('pos.yx', _('Coordinates - Lat, Lng'))))
               
    return result

MAPPING_NAME=re.compile(r"^mapping_(\d+)$")

class CsvImportError(Exception):
    pass

def extract_mapping(posted_fields):
    mapping=defaultdict(lambda: {})
    values={}
    errors=[]
    position=[None, None]
    for key in posted_fields:
        m=MAPPING_NAME.match(key)
        val= posted_fields[key]
        if m and val:
            col=int(m.group(1))
            values[col]=val
            if  val.startswith('pos.'):
                if val=='pos.x':
                    position[0]=col
                elif val=='pos.y':
                    position[1]=col
                elif val=='pos.xy':
                    position=col
                elif val=="pos.yx":
                    position=-col-1
                continue
            if not val in MAPPABLE_FIELDS:
                errors.append(_('Illegal field name %s')%val)
                continue
            val=val.split('.')
            if len(val)==1:
                if mapping.has_key(val[0]):
                    errors.append(_('Field %s already mapped, duplicit column %d')% (val[0], col ))
                    continue
                mapping[val[0]]=col
            elif len(val)==2:
                if mapping[val[0]].has_key(val[1]):
                    errors.append(_('Field %s already mapped, duplicit column %d')% ('.'.join(val), col ))
                mapping[val[0]][val[1]]=col
            else:
                errors.append(_('Invalid field name %s')%val)
    # basic sanity check        
    if  mapping.get('name') is None:
        errors.append(_('Name field must be provided'))
    if isinstance(position, list) and position[0] is None and position[1] is None:
        position = None
    if isinstance(position, list) and (position[0] is None or position[1] is None ):
        errors.append(_('Must provide both geographical coordinates - longitude and latitude'))
        position=None
    if position:
        mapping['position']=position  
    if  not mapping.get('address') and mapping.get('position') is None:
        errors.append(_('Must provide address or location coordinates (or both)'))      
    return dict(mapping), values, errors #defaultdict is not pickable, so convert to nornal doct


POINT_TEMPLATE='POINT(%s %s)'
POSITION_RE=re.compile(r'(\d+[.,]?\d*)\s*[\s,;]\s*(\d+[.,]?\d*)')
class LineError(Exception):
    pass
    
def import_places(temp_file, mapping, name, description=None, private=False, 
                  user=None, existing='update', encoding='utf-8', 
                  error_cb=None, progress_cb=None, context=None):
    log.debug('Processing file %s with this mapping %s', temp_file, mapping)
    errors=[]
    def add_error(line, msg):
        errors.append(_('Line %d - %s') % (line, msg))
        if error_cb:
            error_cb(line, msg)
    exists=PlacesGroup.objects.filter(name=name, private=False).exclude(created_by=user).count()
    if exists:
        add_error(0, _('Collection with same name was created by other user'))
        return
    group, created= PlacesGroup.objects.get_or_create_ns(name=name, created_by=user)
    if created:
        group.description=description
        group.private=private
        group.save(user=user)
    elif existing=='remove':
        group.places.all().delete()
    num_lines = sum(1 for _line in open(temp_file))
    with file(temp_file, 'rb') as f:
        reader=UnicodeReader(f, encoding=encoding)
        headers=reader.next()
        #headers= dict([(headers[col], col) for col in range(len(headers))])
        def get_existing(key):
            if mapping.get(key):
                return l[mapping[key]]
        line=1    
        
        while True:
            line+=1
            log.debug('Processing line %d', line)
            try:
                l=reader.next()
            except StopIteration:
                break
            except Exception, e:
                add_error(line, _('File reading error (%s)')% str(e))
                break
            
            place_name=l[mapping['name']]
            if not place_name.strip():
                add_error(line,_('Empty_place name'))
                continue
            #------------------------------------------------------------
            try:
                place=Place.objects.get(name=place_name, group=group)
            except Place.DoesNotExist:
                place=None
            if place and existing=='skip':
                log.debug('Skipping line %d as existing', line)
            if existing=='update' or not place:
                try:
                    with transaction.commit_on_success():
                        if not place:
                            place=Place(name=place_name, group=group)
                        address=None
                        if mapping.get('address'):
                            address_data=dict([(name, l[mapping['address'][name]]) for name in mapping['address']])
                            address=Address(**address_data)
                        place.description=get_existing('description')
                        place.url=get_existing('url')
                        place.address=address
                        pos_template=POINT_TEMPLATE
                        if mapping.has_key('position'):
                            pos=mapping['position']
                            if isinstance(pos, list):
                                position=pos_template%tuple(map(lambda x: x.replace(',', '.'),(l[pos[0]], l[pos[1]])))
                            else:
                                rev=False
                                if pos<0:
                                    pos=-pos-1
                                    rev=True
                                if not l[pos] :
                                    raise LineError( _('Missing position'))       
                                m=POSITION_RE.search(l[pos])
                                if m and m.lastindex>1:
                                    point=[m.group(1), m.group(2)]
                                    if rev:
                                        point.reverse()
                                    point=map(lambda x: x.replace(',', '.'), point)
                                    position=POINT_TEMPLATE% tuple(point)
                                else:
                                    raise LineError( _('Invalid coordinates (%s)')%l[pos])
                                  
                            place.position=position  
                        else:
                            #geocode from address
                            try:
                                new_address,point=geocode.get_coordinates_remote(address, context=context)
                            except geocode.NotFound:
                                raise LineError( _('Cannot get location for address %s')% unicode(address)) 
                            except remote.TimeoutError:
                                raise LineError(_('Geocoding process is not responding'))
                            except remote.RemoteError, e:
                                raise LineError( _('Geocoding process error (%s)')% str(e))
#                             except geocode.ServiceError, e:
#                                 raise LineError( _('Geocoding Error (%s)')% str(e))
#                             except ValueError,e:
#                                 raise LineError(_('Data Error (%s)')% str(e))
                            place.position=point
                        try:
                            place.save(user=user)
                        except Exception, e:
                            raise LineError( _('Error saving line (%s)')%str(e))
                except LineError,e:
                    add_error(line, e.message)
            if progress_cb:
                progress_cb(line, num_lines)        
    
    return errors   
    
     