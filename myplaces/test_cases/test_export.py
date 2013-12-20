'''
Created on Dec 18, 2013

@author: ivan
'''
import unittest
from django import test
from StringIO import StringIO
from myplaces import format as fmt
from myplaces.models import PlacesGroup
import json
import re



class TestExport(test.TestCase):
    fixtures=["test_data_auth.json", "test_data.json", ]

    def testCSV(self):
        stream=StringIO()
        adapter=fmt.get_fmt_descriptor('CSV').export_adapter(stream)
        
        group=PlacesGroup.objects.get(id=1)
        adapter.export(group, group.places.all())
        
        stream.seek(0)
        
        count=sum([1 for l in stream])
        
        self.assertEqual(count,205 )
        
    def testJSON(self):
        
        stream=StringIO()
        adapter=fmt.get_fmt_descriptor('GEOJSON').export_adapter(stream)
        group=PlacesGroup.objects.get(id=1)
        adapter.export(group, group.places.all())
        
        stream.seek(0)
        
        data=json.load(stream)
        self.assertEqual(len(data['features']), 204)
        
    def testGPX(self):
        
        stream=StringIO()
        adapter=fmt.get_fmt_descriptor('GPX').export_adapter(stream)
        group=PlacesGroup.objects.get(id=2)
        adapter.export(group, group.places.all())
        
        xml= stream.getvalue()
        print xml
        count=len(re.findall('<wpt', xml))
        self.assertEqual(count,86)
        
        
        
        
        
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()