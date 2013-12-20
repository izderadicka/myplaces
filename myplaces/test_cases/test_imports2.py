# encoding=utf-8
'''
Created on Dec 10, 2013

@author: ivan
'''
import unittest

from myplaces.implaces import  LineError
from myplaces import format

import os
CSV_FILE=os.path.join(os.path.split(__file__)[0], './unetice.csv')
JSON_FILE=os.path.join(os.path.split(__file__)[0], './unetice.json')
GPX_PREFIX=os.path.join(os.path.split(__file__)[0], './gpx')


class TestImports3(unittest.TestCase):
    
    def test_desc(self):
        desc=format.get_fmt_descriptor('CSV')
        self.assertEqual(desc.name, 'CSV')
        self.assertEqual(desc.desc, 'CSV (Comma Separated Values)')
        self.assertEqual(desc.sort_order, 1)
        self.assertEqual(desc.mime, 'text/csv')
        self.assertEqual(desc.extensions, ['csv'])

    def testGPX(self):
        GPXFileReader=format.get_fmt_descriptor('GPX').reader
        r=GPXFileReader(os.path.join(GPX_PREFIX, 'favorites.gpx'))
        self.assertEqual(r.count(), 4)
        places = list(r)
        self.assertEqual(len(places),4)
        p=places[0]
        print p
        self.assertEqual(p['name'], u'u ondřeje')
        self.assertEqual(p['address']['street'], u'Výpadová 215/9')
        self.assertEqual(p['address']['country'], u'Czech Republic')
        
        p=places[1]
        self.assertEqual(p['url'], u'http://www.nakopci.com')
        self.assertEqual(p['address']['phone'], u'+420702061564')
        
        r=GPXFileReader(os.path.join(GPX_PREFIX, 'test.gpx'))
        self.assertEqual(r.count(), 1)
        places = list(r)
        self.assertEqual(len(places),1)
        p=places[0]
        self.assertEqual(p['address']['phone'], u'483120002')
        self.assertEqual(p['name'], u'Test')
        
        r=GPXFileReader(os.path.join(GPX_PREFIX, 'pr-churches.gpx'))
        self.assertEqual(r.count(), 161)
        places = list(r)
        self.assertEqual(len(places),161)
        p=places[0]
        self.assertEqual(p['name'], u'Buen Pastor')
        
        r=GPXFileReader(os.path.join(GPX_PREFIX, 'pr-churches.gpx'))
        self.assertEqual(r.count(), 161)
        places = list(r)
        self.assertEqual(len(places),161)
        
        r=GPXFileReader(os.path.join(GPX_PREFIX, 'H-CampingSite.gpx'))
        self.assertEqual(r.count(), 370)
        places = list(r)
        self.assertEqual(len(places),370)
        
#         r=GPXFileReader(os.path.join(GPX_PREFIX, 'us_starbucks.gpx'))
#         self.assertEqual(r.count(), 8881)
#         places = list(r)
#         self.assertEqual(len(places),8881)
        
        
    def testReader(self):
        CSVFileReader=format.get_fmt_descriptor('CSV').reader
        r=CSVFileReader(CSV_FILE, {'name':0, 'address':{'street':1, 'city':2, 'country':3}, 'position':-5,
                                   'url':5})
        
        count=0
        errors=0
        while True:
            try:
                l=r.next()
                count+=1
            except LineError:
                errors+=1
            except StopIteration:
                break
                
            
            
        self.assertEqual(count, 86)
        self.assertEqual(errors, 2)
        
    def testGeoJson(self):
        reader=format.get_fmt_descriptor('GEOJSON').reader(JSON_FILE)
        places=list(reader)
        self.assertEqual(len(places), 86)
        self.assertTrue(places[0]['address'])


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()