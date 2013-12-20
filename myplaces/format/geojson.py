'''
Created on Dec 14, 2013

@author: ivan
'''

from ..format import ExportAdapter, export_adapter, import_reader, FileReader
import json
from ..implaces import LineError
from django.utils.translation import ugettext as _
import types
from _utils import verify_pos

NAME='GEOJSON'
DESCRIPTION='GeoJSON (JSON Geometry Format)'
SORT=3
MIME='application/json'
EXTENSIONS='json,geojson'

@import_reader
class GeoJsonReader(FileReader):
    def __init__(self, file_name, extra_params=None):
        with file(file_name, 'rb') as f:
            data=json.load(f)
        self._features=data['features']
        self._iter=iter(self._features)
        
            
    def count(self):
        return len(self._features)  
    
    def next(self):
        feature=self._iter.next()
        def set_ifex(name):
            if props.get(name):
                line[name]=props[name]
        if feature['geometry']['type']!='Point':
            raise LineError(_('Feature is not a Point'))
        line={'position': tuple(feature['geometry']['coordinates'])}
        verify_pos(*line['position'])
        try:
            props=feature['properties']
        except KeyError:
            raise LineError(_('Feature properties are missing'))
        try:
            line['name']=props['name']
        except KeyError:
            raise LineError(_('Name property is mandatory'))
        
        set_ifex('url')
        set_ifex('description')
        
        adr=props.get('address')
        if adr:
            if isinstance(adr, types.StringTypes):
                adr={'unformatted':adr}
            elif isinstance(adr, dict):
                for k in adr:
                    if k not in ['street', 'city', 'county', 'state', 'country', 'postal_code', 'phone', 'email']:
                        del adr[k]  
            else:
                raise LineError(_('Invalid address format'))
            line['address']=adr
        return line
        
        
                                  
                               
        

@export_adapter
class GeoJsonExport(ExportAdapter):
    
    def export(self, group, places):
        self.response.write(group.as_geojson(places, details=True))

