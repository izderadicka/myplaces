'''
Created on Jun 7, 2013

@author: ivan
'''

from django.utils.translation import ugettext as _
import tempfile
import logging
from myplaces import geocode, remote
from django.contrib.gis.geos.point import Point
import traceback
log=logging.getLogger('mp.implaces')
from models import Place, Address, PlacesGroup, MaxObjectsLimitReached
from django.db import transaction
import format as fmt


def save_file(uploaded_file):
    temp_file=tempfile.NamedTemporaryFile(suffix='.upload', prefix='myplaces-', delete=False)
    with temp_file:
        for chunk in uploaded_file.chunks():
            temp_file.write(chunk)
            
    return temp_file.name



class LineError(Exception):
    pass
    
def import_places(temp_file, extra_params, name, description=None, private=False, 
                  user=None, existing='update', encoding='utf-8', 
                  error_cb=None, progress_cb=None, context=None,
                  format='CSV'):
    log.debug('Processing file %s with this extra params %s', temp_file, extra_params)
    errors=[]
    def add_error(line, msg):
        errors.append(_('Line %d - %s') % (line, msg))
        if error_cb:
            error_cb(line, msg)
    file_reader=fmt.get_fmt_descriptor(format).reader(temp_file, extra_params)
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
    num_lines = file_reader.count()
    with file_reader:  
        line=0    
        while True:
            line+=1
            log.debug('Processing line %d', line)
            try:
                l=file_reader.next()
            except StopIteration:
                break
            except LineError, e:
                add_error(line, e.message)
                continue
            except Exception, e:
                add_error(line, _('File reading error (%s)')% str(e))
                traceback.print_exc()
                break
            
            place_name=l['name']
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
                        if l.get('address'):
                            address=Address(**l['address'])
                        place.description=l.get('description')
                        place.url=l.get('url')
                        if l.get('position'):
                            pos=l['position']      
                            place.position=Point(*pos, srid=4326)  
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
                            if address:
                                address.save(user=user)
                                place.address=address
                            place.save(user=user)
                        except MaxObjectsLimitReached:
                            add_error(line, _('Reached limit of records per user'))   
                            break
                        except Exception, e:
                            raise LineError( _('Error saving line (%s)')%str(e))
                except LineError,e:
                    add_error(line, e.message)
            if progress_cb:
                progress_cb(line, num_lines)        
    
    return errors   
    
     