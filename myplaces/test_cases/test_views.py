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
        res=self.client.get('/mp/group/1/edit/')
        self.assertTrue(res.status_code, 403)
        res=self.client.post('/login/', {'username':'admin', 'password':'admin'})
        res=self.client.get('/mp/group/1/edit/')
        
        self.assertTrue(res.status_code, 200)
        self.assertTrue(res.content is not None and len( res.content)>0)
        
    
    def test_pages_public(self):
        res=self.client.get('/mp/group/1/')
        self.assertContains(res, '{"type":"FeatureCollection", "features":', status_code=200)
        res=self.client.get('/mp/groups/')
        self.assertContains(res, u'<span class="group_title">', status_code=200)
        res=self.client.get('/mp/places/1/')
        self.assertContains(res, '<li data-pk', status_code=200)
        res=self.client.get('/mp/map/1/')
        self.assertContains(res, '<div id="my_map"', status_code=200)
        
    def test_pages_restricted(self):
        self.client.login(username='admin', password='admin')
        res=self.client.get('/mp/group/1/edit/') 
        self.assertContains(res, '<div id="head-form">', status_code=200)
        res=self.client.get('/mp/group/1/edit/header/') 
        self.assertContains(res, '<form method="POST" action="/mp/group/1/edit/header">', status_code=200)
        res=self.client.get('/mp/import/1/') 
        self.assertContains(res, '<form ', status_code=200)
        
        
        
        
        