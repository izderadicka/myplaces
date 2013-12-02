'''
Created on Sep 30, 2013

@author: ivan
'''
import unittest
from myplaces.voronoi import move_point, check_outside, voronoi2
import numpy as np
from django import test
import json
import subprocess
import os
from myplaces import remote

class TestVoronoi(unittest.TestCase):


    def test_shift(self):
        bbox=(0, 0, 120, 120)
        start=np.array([-644.32751612,   -4.24797169])
        end=np.array([  5.83859719,  57.58052858])
        
        p= move_point(start, end, bbox)
        
        self.assertTrue(p[0]>=0 and p[1]>=0 and p[0]<=120 and p[1]<=120)
        
    def test_voronoi(self):
        bbox=(-20, -20, 120, 120)
        points=np.random.rand(100,2)*100
        lines=voronoi2(points, bbox)
        self.assertTrue(len(lines)>150)
        
        for i,l in enumerate(lines):
            self.assertTrue(not check_outside(l[0], bbox), 'line %d point x outside bbox'%i)
            self.assertTrue(not check_outside(l[1], bbox), 'line %d point y outside bbox'%i)
            
    def test_3(self):
        points=np.array([[19.38,2.55], [98.39,51.02], [54.71, 71.43]])
        bbox=(-50, -50, 150, 150)
        lines=voronoi2(points, bbox)
        print lines
        self.assertEqual(len(lines), 3)
        for i,l in enumerate(lines):
            self.assertTrue(not check_outside(l[0], bbox), 'line %d point x outside bbox'%i)
            self.assertTrue(not check_outside(l[1], bbox), 'line %d point y outside bbox'%i)


import myplaces.views  as views          
class TestVoronoiGeojson(test.TestCase):
    fixtures=["test_data_auth.json", "test_data.json", ]
    
    def setUp(self):
        remote.init()
        manage=os.path.join(os.path.split(__file__)[0], '../../manage.py')
        self.p=subprocess.Popen(['python', manage,  'process_server'], shell=False)
      
    def tearDown(self):
        self.p.kill()
    
    def test_json_view(self):
        req= test.RequestFactory().get('/mp/gejson/group/voronoi/1')
        resp=views.group_voronoi_geojson(req, 1)
        self.assertEqual(resp.status_code, 200)
    def test_json(self):
        data=self.client.get('/mp/geojson/group/voronoi/1').content
        data=json.loads(data)
        lines=data['features'][0]['geometry']['coordinates']
        self.assertTrue(len(lines)>200)
        bbox=data['properties']['bbox']
        self.assertEqual(len(bbox), 4)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testShift']
    unittest.main()