# coding=utf-8
'''
Created on Jun 14, 2013

@author: ivan
'''

import logging
import types
from urllib2 import URLError
import time
from myplaces import remote
import zmq
log=logging.getLogger('mp.geocode')
import re
import json
from geopy import geocoders, util 
from geopy.geocoders.base import GeocoderError
from django.contrib.gis.geos import Point
from models import Address


class CoderMixin(object):
    def address_to_string(self,adr):
        if not isinstance(adr, types.StringTypes):
            adr=unicode(adr)
            if not adr:
                raise ValueError('empty address')   
        return adr
    
    def try_be_smart(self,address, original_address):
        # Try to locate at least approximately - e.g. remove first address segment and try again
        address=map(lambda s: s.strip(),re.split(r'[,;]', address))
        if len(address)>2:
                address=', '.join(address[1:])
                return address
        
        return None
        
    def reverse(self, point):
        places=super(CoderMixin, self).geocode(point, exactly_one=False)
        if places:
            return places[0]
        raise NotFound
    def geocode (self, adr):
        address=self.address_to_string(adr)
        while True:
            try:
                places=super(CoderMixin, self).geocode(address, exactly_one=False)
                break
            except NotFound:
                
                address= self.try_be_smart(address, adr)
                if not address:
                    raise NotFound
            except (ValueError, URLError, IOError),e:
                log.error('Geocode service error - %s', e)
                raise ServiceError('Geocode service error - %s' % str(e))
        #sanity check - found address should be in city(or county for huge cities like London) provided.
        for  p in places:
            
            if (p[0].city and p[0].city.lower() in address.lower()) or \
               (p[0].county and p[0].county.lower() in address.lower()):
                return p
        #else return what we got
        if places:
            return places[0]
        raise NotFound
    
class NominatimAddressAdapter(object):
    def __init__(self, address):
        self.a=address
        
    def _apply_fixes(self, string, fixes):
        if not string:
            return string
        for regexp, replace in fixes:
            regexp=re.compile(regexp, re.IGNORECASE| re.UNICODE)
            if regexp.search(string):
                string= regexp.sub(replace,string)
        return string
    
    
    def fix_country(self):
        return self.a.country
    CITY_FIXES=[(ur'^(.+)\s+(\d{1,2})(?=$|\s)', r'\1'),
                (ur'^(.+)\s+([IVX]{1,5})$', r'\1'),
                (ur'\s(n\.)(?=\s)', '')]
    def fix_city(self, ext=None):
        city=ext or self.a.city
        return self._apply_fixes(city, self.CITY_FIXES)
    
    ONE_LETTER=re.compile(r'(?<=\s)([^\W\d_]\.)|^([^\W\d_]\.)', re.UNICODE)
    STREET_FIXES=[(ur'nám\.', ''),
                  (ur'ul\.', ''),
                  (ur'nábř\.', ''),
                  (ur'tř\.', ''),
                  (ur'ulice', '')]
    def fix_street(self, ext=None):
        street=ext or self.a.street
        street=self._apply_fixes(street, self.STREET_FIXES)
        clean=self.ONE_LETTER.sub('',street).strip()
        if clean:
            street=clean
        return street
    
    PC_FIX=re.compile(r'(^|\s)(\d{3} \d{2})(\s|$)')      
    def __unicode__(self):
        if self.a.street or self.a.city:
            adr=[]
            for field in ('street', 'city', 'country'):
                s=getattr(self, 'fix_'+field)() if hasattr(self,'fix_'+field) else None
                if s:
                    adr.append(s)
            return u', '.join(adr)
        else:
            string= self.a.unformatted
            if not string:
                return ''
            adr=map(lambda s: s.strip(), re.split(r'[,;]', string))
            length=len(adr)
            res=[]
            for i,seg in enumerate(adr):
                if length>1 and i==0:
                    seg=self.fix_street(seg)
                if length>1 and i>0:
                    #TODO - this is temporary fix for CZ postal codes
                    seg=self.PC_FIX.sub('', seg)
                    seg=self.fix_city(seg)
                
                if seg:
                    res.append(seg)
            return u', '.join(res)
        

class OSMNominatim(CoderMixin, geocoders.OpenMapQuest):
    def __init__(self, format_string='%s'):
        super(OSMNominatim, self).__init__(format_string=format_string)
        self.url='http://nominatim.openstreetmap.org/search.php?format=json&addressdetails=1&%s'
    
    def address_to_string(self,adr): 
        if isinstance(adr, Address):
            adapter=NominatimAddressAdapter(adr)
        elif isinstance(adr, types.StringTypes):
            adapter=NominatimAddressAdapter(Address(unformatted=adr))
        else:
            raise ValueError('Invalid address type %s' % type(adr))
        string=unicode(adapter)
        if not string:
                raise ValueError('Empty address')   
        return string
    
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
        street=address.get('road') or address.get('pedestrian') or address.get('village') or address.get('hamlet')
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
        
class Google(CoderMixin, geocoders.GoogleV3):   
    REQUESTS_LIMIT=0.2
    def __init__(self, *args, **kwargs):
        super(Google,self).__init__(*args, **kwargs)
        
    
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
            _gcoders[1]=Google()
        return _gcoders[1]
    else:
        if not _gcoders[0]:
            _gcoders[0]=OSMNominatim()
        return _gcoders[0]

def get_coordinates(address, alternate_geocoder=False):
   
    gcoder=_get_geocoder_instance(alternate_geocoder)
    place=gcoder.geocode(address)
    address, (lat, lng)=place
    
    return address, Point(lng, lat, srid=4326)


@remote.is_remote
def geocode_remote(adr, alternate=False, reverse=False, timer=None):
    #throttle requests to geocoding service
    if timer:
        nr=timer.get('next_run') or time.time()
        wait=nr-time.time()
        while wait>0:
            time.sleep(wait)
            wait=nr-time.time()
            
    gcoder=_get_geocoder_instance(alternate)
    try:
        place=gcoder.geocode(adr) if not reverse else gcoder.reverse(adr)
    except NotFound:
        place= None, (None, None)
    if timer:
        delay=gcoder.REQUESTS_LIMIT if hasattr(gcoder, 'REQUESTS_LIMIT') else 0
        timer['next_run']=time.time()+delay
    return place


GC_ADDR='tcp://127.0.0.1:10009'  
def get_coordinates_remote(adr, alternate=False, reverse=False, context=None):      
    ctx=context or remote.context()   
    socket=ctx.socket(zmq.REQ)  
    socket.connect(GC_ADDR)
    
    pos=remote.call_remote(socket, 'geocode_remote', (adr, alternate, reverse),  timeout=60)
    
    if not pos[0]:
        raise NotFound
    
    address, (lat, lng)=pos
    return address, Point(lng, lat, srid=4326)

def get_address_remote(location, alternate=False, context=None):
    return get_coordinates_remote(location, alternate, True, context)
    
    
