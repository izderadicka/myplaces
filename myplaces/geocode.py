'''
Created on Jun 14, 2013

@author: ivan
'''

import logging
import types
from urllib2 import URLError
import time
import threading
log=logging.getLogger('mp.geocode')
import re
import json
from geopy import geocoders, util 
from geopy.geocoders.base import GeocoderError
from django.contrib.gis.geos import Point

from models import Address


gcoders=[geocoders.GoogleV3(), geocoders.OpenMapQuest()]

class OSMNominatim(geocoders.OpenMapQuest):
    def __init__(self, format_string='%s'):
        super(OSMNominatim, self).__init__(format_string=format_string)
        self.url='http://nominatim.openstreetmap.org/search.php?format=json&addressdetails=1&%s'
    PC_FIX=re.compile(r'(\d{3}) (\d{2})')    
    def geocode(self, string, exactly_one=True):
        if not string:
            raise ValueError('empty address')
           
        #fix CZ postal codes for search
        string=OSMNominatim.PC_FIX.sub('\1\2', string)
        return geocoders.OpenMapQuest.geocode(self, string, exactly_one=exactly_one)
    
    def parse_json(self, page, exactly_one=True):
        """Parse address, latitude, and longitude from an JSON response."""
        if not isinstance(page, basestring):
            page = util.decode_page(page)
        resources = json.loads(page)
        
        if not resources:
            raise NotFound()
        
        if exactly_one and len(resources)!=1:
            raise ValueError('Found more then one places')
        
        
        if exactly_one:
            return self._parse_resource(resources[0])
        return [self._parse_resource(r) for r in resources]
        
    def _parse_resource(self, resource):
        address = resource['address']
        log.debug('Matched address is %s', address)
        parsed_address=Address()
        street=address.get('road') or address.get('pedestrian')
        if address.get('house_number') and street:
            street+=' '+address['house_number']
        parsed_address.street=street
        parsed_address.city=address.get('city')
        parsed_address.country=address.get('country')
        parsed_address.county=address.get('county')
        parsed_address.state=address.get('state')
        
        
        latitude = resource['lat'] or None
        longitude = resource['lon'] or None
        if latitude and longitude:
            latitude = float(latitude)
            longitude = float(longitude)
        
        return (parsed_address, (latitude, longitude))
        
class Google(geocoders.GoogleV3):   
    REQUESTS_LIMIT=0.2
    def __init__(self, *args, **kwargs):
        super(Google,self).__init__(*args, **kwargs)
        self.last_request=0
       
        
    def geocode_url(self, url, exactly_one=True):
        time_from_prev_call= time.time() - self.last_request
        #HACK: This is bit stupid way to try to keep certain limit of requests per minute
        while  time_from_prev_call < Google.REQUESTS_LIMIT:
            time.sleep(Google.REQUESTS_LIMIT-time_from_prev_call)
            time_from_prev_call= time.time() - self.last_request
        self.last_request=time.time()
        return geocoders.GoogleV3.geocode_url(self, url, exactly_one=exactly_one)
    def parse_json(self, page, exactly_one=True):
        if not isinstance(page, basestring):
            page = util.decode_page(page)
        self.doc = json.loads(page)
        #print self.doc
        places = self.doc.get('results', [])
    
        if not places:
            try:
                geocoders.googlev3.check_status(self.doc.get('status'))
            except GeocoderError, e:
                log.info('Google error - %s', e)
        
            raise NotFound()
        
        elif exactly_one and len(places) != 1:
            raise ValueError(
                "Didn't find exactly one placemark! (Found %d)" % len(places))
        
        if exactly_one:
            return self._parse_place(places[0])
        else:
            return [self._parse_place(place) for place in places]
        
    def _parse_place(self,place):
        location = place.get('formatted_address')
        address=Address()
        street_number= ''
        def set_if_type(attr,type):
            if type in part['types']:
                setattr(address, attr,part['long_name'])
        for part in place.get('address_components'):
            set_if_type('street','route')
            set_if_type('city','locality')
            set_if_type('county', 'administrative_area_level_2')
            set_if_type('state', 'administrative_area_level_2')
            set_if_type('country', 'country')
            set_if_type('postal_code','postal_code')
            if not part['types'] or 'street_number' in part['types']:
                street_number=part['long_name']
                
        if address.street and street_number:
            address.street+=' '+street_number
            
        latitude = place['geometry']['location']['lat']
        longitude = place['geometry']['location']['lng']
        return (address, (latitude, longitude))
        
class NotFound(Exception):
    pass

class ServiceError(Exception):
    pass

_gcoders=[None, None]

def _get_geocoder_instance(alternate_geocoder=False):
    if alternate_geocoder:
        if not _gcoders[1]:
            _gcoders[1]=OSMNominatim()
        return _gcoders[1]
    else:
        if not _gcoders[0]:
            _gcoders[0]=Google()
        return _gcoders[0]

def get_coordinates(address, alternate_geocoder=False, allow_approximate=True):
    if not isinstance(address, types.StringTypes):
        address=unicode(address)
    gcoder=_get_geocoder_instance(alternate_geocoder)
    while True:
        try:
            places=gcoder.geocode(address, exactly_one=False)
            break
        except NotFound:
            # Try to localte at least approximatelly - e.g. remove first address segment and try again
            address=map(lambda s: s.strip(),re.split(r'[,;]', address))
            if len(address)>2 and allow_approximate:
                address=', '.join(address[1:])
            else:
                raise NotFound('Address %s not found on map'%address )
        except (ValueError, URLError, IOError),e:
            log.error('Geocode service error - %s', e)
            raise ServiceError('Geocode service error - %s' % str(e))
        
    address, (lat, lng)=places[0]
    
    return address, Point(lng, lat, srid=4326)
