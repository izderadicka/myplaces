'''
Created on Dec 14, 2013

@author: ivan
'''
try:
    from lxml import etree as ElementTree
    XML_PARSER='lxml'
except ImportError:
    from xml.etree import ElementTree
    XML_PARSER='python'
    
# from xml.etree import ElementTree
from . import FileReader, import_reader, export_adapter, ExportAdapter
from ..implaces import LineError
from _utils import verify_pos

NS= {'gpx':'http://www.topografix.com/GPX/1/1',
         'ext': 'http://www.garmin.com/xmlschemas/GpxExtensions/v3',
         'ol': 'http://www.topografix.com/GPX/gpx_overlay/0/3'
         }

ElementTree.register_namespace('gpxx', NS['ext'])
                            

NAME='GPX'
DESCRIPTION='GPX (GPS Exchange Format)'
SORT=2
MIME='application/gpx+xml'
EXTENSIONS='gpx'

@import_reader
class GPXFileReader(FileReader):
   
    def __init__(self, fileName, extra_params=None, count_items=True):
        self._count=None
        if count_items:
            root=ElementTree.parse(fileName)
            self._count=len(root.findall('gpx:wpt', NS))
        self._iter=ElementTree.iterparse(fileName)
    def count(self):
        return self._count
    
    def next(self):
        while True:
            event, elem= self._iter.next()
            if event=='end' and self._is_elem(elem, 'wpt', 'gpx'):
                return self._map_place(elem)
            
    def _map_place(self, elem):
        place={}
        try:
            pos=(float(elem.get('lon')), float(elem.get('lat')))
        except ValueError:
            raise LineError(_('Invalid location format'))
        place['position']= pos
        verify_pos(*pos)
        place['name']=self._find_and_get(elem,'gpx:name')
        if not place['name']:
            place['name']=self._find_and_get(elem, './gpx:extensions/ol:label/ol:label_text')
            
        if not place['name']:
            raise LineError(_('Name is missing'))
        
        place['description']=self._find_and_get(elem, 'gpx:desc')
        address={}
        adr_elem= elem.find('./gpx:extensions/ext:WaypointExtension/ext:Address', NS)
        if adr_elem and len(adr_elem):
            street=adr_elem.findall('ext:StreetAddress', NS)
            street= u', '.join(map(lambda s: s.text,street))
            address['street']=street or None
            address['city']=self._find_and_get(adr_elem, 'ext:City')
            address['state']=self._find_and_get(adr_elem, 'ext:State')
            address['postal_code']=self._find_and_get(adr_elem, 'ext:PostalCode')
            address['country']=self._find_and_get(adr_elem, 'ext:Country')
        
        phones=elem.findall('./gpx:extensions/ext:WaypointExtension/ext:PhoneNumber', NS)
        for phone in phones:
            if not phone.get('Category') or phone.get("Category") in ('Phone', 'Work', 'Mobile'):
                address['phone']=phone.text
                break
            
        link=elem.find('gpx:link', NS)
        if link is not None:
            place['url']=link.get('href')
            
        if reduce(lambda x,y: x or y, address.values(), False):
            place['address']=address
        return place
    
    def _find_and_get(self, elem, tag ):
        e=elem.find(tag, NS)
        if e is not None:
            return e.text
             
    def _is_elem(self, elem, tag, prefix):
        return elem.tag == '{%s}%s' % (NS.get(prefix), tag)
        

@export_adapter
class GpxExporter(ExportAdapter):
    def export(self, group, places):
        def qname(prefix, name):
            if XML_PARSER=='lxml' and prefix=='gpx':
                return name
            return ElementTree.QName(NS[prefix], name)
        root_args={}
        nsmap={None: NS['gpx'], 
                        'gpxx':NS['ext'],
                        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
                        }
        if XML_PARSER=='lxml':
            root_args['nsmap']=nsmap
        
        root=ElementTree.Element(qname('gpx','gpx'), {
                qname('gpx','version'):'1.1', 
                qname('gpx','creator'):'MyPlaces',
                ElementTree.QName(nsmap['xsi'], 'schemaLocation'): 'http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd http://www.garmin.com/xmlschemas/GpxExtensions/v3 http://www8.garmin.com/xmlschemas/GpxExtensions/v3/GpxExtensionsv3.xsd',
                },
                **root_args)
        tree=ElementTree.ElementTree(root)
        meta=ElementTree.SubElement(root, qname('gpx', 'metadata'))
        ElementTree.SubElement(meta, qname('gpx', 'name')).text=group.name
        if group.description:
            ElementTree.SubElement(meta, qname('gpx', 'desc')).text=group.description
        for place in places:
            wpt=ElementTree.SubElement(root, qname('gpx', 'wpt'), 
                {qname('gpx', 'lon'): str(place.position.x),
                 qname('gpx', 'lat'): str(place.position.y)})
            ElementTree.SubElement(wpt, qname('gpx', 'name')).text=place.name
            if place.description:
                ElementTree.SubElement(wpt, qname('gpx', 'desc')).text=place.description
            if place.url:
                ElementTree.SubElement(wpt, qname('gpx', 'link'), {qname('gpx', 'href'):place.url})
            if place.address:
                ext=ElementTree.SubElement(wpt, qname('gpx', 'extensions'))
                ext=ElementTree.SubElement(ext, qname('ext', 'WaypointExtension'))
                if place.address.street or place.address.city or place.address.state or \
                    place.address.country or place.address.postal_code:
                    adr=ElementTree.SubElement(ext, qname('ext', 'Address'))
                    if place.address.street:
                        ElementTree.SubElement(adr, qname('ext', 'StreetAddress')).text=place.address.street
                    if place.address.city:
                        ElementTree.SubElement(adr, qname('ext', 'City')).text=place.address.city
                    if place.address.state:
                        ElementTree.SubElement(adr, qname('ext', 'State')).text=place.address.state
                    if place.address.country:
                        ElementTree.SubElement(adr, qname('ext', 'Country')).text=place.address.country
                    if place.address.postal_code:
                        ElementTree.SubElement(adr, qname('ext', 'PostalCode')).text=place.address.postal_code
                if place.address.phone:
                    ElementTree.SubElement(ext, qname('ext', 'PhoneNumber')).text=place.address.phone
                    
                    
                
                 
        
        output_args={}
        if XML_PARSER=='python':
            output_args['default_namespace']=NS['gpx']
        tree.write(self.response, encoding='utf-8', xml_declaration=True, **output_args)
