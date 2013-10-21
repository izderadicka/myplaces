# -*- coding: utf-8 -*- 
'''
Created on Aug 27, 2013

@author: ivan
'''

from django import test
import unittest

class TestViews(test.TestCase):
    fixtures=["test_data.json", "test_data_auth.json"]
    
    def test_login(self):
        res=self.client.get('/mp/')
        self.assertTrue(res.status_code, 200)
        res=self.client.post('/login/', {'username':'admin', 'password':'admin'})
        res=self.client.get('/mp/')

        self.assertTrue(res.status_code, 200)
        self.assertTrue(res.content is not None and len( res.content)>0)
        
    
    def test_pages_public(self):
        res=self.client.get('/mp/geojson/group/1')
        self.assertContains(res, '{"type":"FeatureCollection", "features":', status_code=200)
        res=self.client.get('/mp/')
        self.assertContains(res, u'<div id="content">', status_code=200)
        
        res=self.client.get('/mp/map/1/')
        self.assertContains(res, '<div id="map"', status_code=200)
        
   
        
        
        
        
        