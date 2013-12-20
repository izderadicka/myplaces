'''
Created on Dec 14, 2013

@author: ivan
'''
import csv
import codecs
import re
from collections import defaultdict
from myplaces.format import FileReader, ImportFormAddon, import_reader, import_addon, ExportAdapter, export_adapter
from myplaces.implaces import LineError
from _utils import verify_pos
from myplaces.models import Place
from django.utils.translation import ugettext as _
from StringIO import StringIO


#mandatory module fields
NAME='CSV'
DESCRIPTION='CSV (Comma Separated Values)'
SORT=1
MIME="text/csv"
EXTENSIONS="csv"


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

@import_reader
class CSVFileReader(FileReader):
    def __init__(self, temp_file, mapping, encoding='utf-8'):
        with open(temp_file) as f:
            self._count = sum(1 for _line in f)
        self._file=file(temp_file, 'rb')
        self._reader=UnicodeReader(self._file, encoding=encoding)
        _headers=self._reader.next() # reads out header
        self._mapping=mapping
        
        
    class Record(object):
        POSITION_RE=re.compile(r'(-?\d+[.,]?\d*)\s*[\s,;]\s*(-?\d+[.,]?\d*)')
        def __init__(self, line, mapping):
            self._mapping=mapping
            self._line=line
            self._calculated={}
            
            if mapping.has_key('address'):
                self._calculated['address']=self._format_address()
                
            if mapping.has_key('position'):
                self._calculated['position']=self._format_position()
                
        def _format_address(self):
            return dict([(name, self._line[self._mapping['address'][name]]) for name in self._mapping['address']])
        
        def _format_position(self):
            def conv_point(point):
                try:
                    return tuple(map(lambda x: float(x.replace(',', '.')), point))
                except ValueError:
                    raise LineError(_('Invalid value of coordinates'))
            pos=self._mapping['position']
            if isinstance(pos, list):
                position=conv_point((self._line[pos[0]], self._line[pos[1]]))
            else:
                rev=False
                if pos<0:
                    pos=-pos-1
                    rev=True
                if not self._line[pos] :
                    return None    
                m=self.POSITION_RE.search(self._line[pos])
                if m and m.lastindex>1:
                    point=[m.group(1), m.group(2)]
                    if rev:
                        point.reverse()
                    position=conv_point(point)
                else:
                    raise LineError( _('Invalid location coordinates (%s)')%self._line[pos])
                
            return position  
            
        def get(self, key, default=None):
            try:
                return self.__getitem__(key)
            except KeyError:
                return default
        
        def __getitem__(self,key):
            if self._calculated.has_key(key):
                return self._calculated[key]
            if self._mapping.has_key(key):
                return self._line[self._mapping[key]]
            raise KeyError
        
        
    def next(self):
        line=self._reader.next()
        return self._validate(CSVFileReader.Record(line, self._mapping))    
        
    def _validate(self,rec):   
        if not rec.get('name'):
            raise LineError(_('Empty place name'))
        if self._mapping.has_key('position'):
            pos=rec['position']
            if not pos:
                raise LineError(_('Location coordinates missing, although they\'re mapped'))
            else:
                verify_pos(*pos)
        
        return rec
            
    def count(self):
        return self._count-1 if self._count>1 else 0
    
    def close(self):
        self._file.close()

@import_addon
class CSVImportExtra(ImportFormAddon):
    template='upload2-csv.html'
    def extend_context(self, file_name, ctx, encoding='utf-8'):
        with file(file_name, 'rb') as f:
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
            
        ctx['headers']=headers
        ctx['max_lens']=length
        ctx['sample_lines']=lines
        ctx['mappable_fields']=self._get_mappable_fields()
        
        
    MAPPING_NAME=re.compile(r"^mapping_(\d+)$")
    def process_form(self, data):
        mapping=defaultdict(lambda: {})
        values={}
        errors=[]
        position=[None, None]
        for key in data:
            m=self.MAPPING_NAME.match(key)
            val= data[key]
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
                if not val in self.MAPPABLE_FIELDS:
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
        return dict(mapping) , errors #defaultdict is not pickable, so convert to nornal doct


    MAPPABLE_FIELDS=['name', 'description', 'url',
                 'address.street', 'address.city', 'address.county', 'address.state', 
                 'address.postal_code',
                 'address.country', 'address.unformatted', 'address.email', 'address.phone']

    def _get_mappable_fields(self):
#     skip_fields=Auditable._meta.get_all_field_names()  # @UndefinedVariable
#     skip_fields.extend(['id', 'group', 'position', 'address'])
#     fields=[name for name  in Place._meta.get_all_field_names() if name not in skip_fields]  # @UndefinedVariable
#     fields=map(lambda n: (n, unicode(Place._meta.get_field(n).verbose_name)), fields)  # @UndefinedVariable
        base_model=Place
        result=[]
        def fmt_name(model, field):
            max_length=unicode(model._meta.get_field(field).max_length)
            return unicode(model._meta.get_field(field).verbose_name) +u' (%s)'%max_length
        for f in self.MAPPABLE_FIELDS:
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

@export_adapter
class CSVAdapter(ExportAdapter):  
    HEADERS_GENERAL=['name', 'description', 'url', 'position'] 
    HEADERS_ADDRESS=['street', 'city', 'county', 'state', 'country', 'postal_code', 'phone', 'email']
    
    def export(self, group, places):
        writer=csv.DictWriter(self.response, self.HEADERS_GENERAL+self.HEADERS_ADDRESS)
        writer.writeheader()
        def get_encoded(o, name):
            val=getattr(o, name)
            if isinstance(val, unicode):
                val=val.encode('utf-8')
            return val
        for p in places:
            line={}
            for name in self.HEADERS_GENERAL[:-1]:
                line[name]=get_encoded(p,name) or ''
            pos=','.join(map(lambda s: str(s),[p.position.y,p.position.x]))
            line['position']=pos
            adr=p.address
            if adr:
                for name in self.HEADERS_ADDRESS:
                    line[name]=get_encoded(adr,name)
                    
            writer.writerow(line)
                    
        
                    
    
    


