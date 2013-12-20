# -*- coding: utf-8 -*- 
"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from  myplaces import implaces
import os
import sys
#os.environ['DJANGO_SETTINGS_MODULE']='settings'
from django.test import TestCase as DjangoTestCase
from django.contrib.auth.models import User

from django.test.utils import setup_test_environment
setup_test_environment()

import logging
from myplaces import format as fmt
logging.basicConfig(level=logging.DEBUG)

CSV_FILE=os.path.join(os.path.split(__file__)[0], './pivovary.csv')
class ImportTest1(DjangoTestCase):
    def test_headers(self):
        ctx={}
        addon=fmt.get_fmt_descriptor('CSV').import_addon()
        addon.extend_context(CSV_FILE, ctx)
        headers, length, lines=ctx['headers'], ctx['max_lens'], ctx['sample_lines']
        print headers
        print length
        print lines
        self.assertTrue(len(headers)>5)
        self.assertEqual(len(headers), len(length))
        self.assertEqual(len(lines),5)
        
    
    def test_mapping(self):
        addon=fmt.get_fmt_descriptor('CSV').import_addon()
        fields= addon._get_mappable_fields()
        self.assertTrue(len(fields)>5)
        print fields
        
GPX_FILE=os.path.join(os.path.split(__file__)[0], 'gpx/favorites.gpx')        
from myplaces.models import Place 
class ImportTest2(DjangoTestCase):
    fixtures=[ "test_data_auth.json", ] 
    def test_import(self):
        user=User.objects.get(username='admin')
        mapping= {u'url': 4, 'position': -4, u'name': 0, u'address': {u'unformatted': 1, u'phone': 5, u'email': 6}}
        errors=implaces.import_places(CSV_FILE, mapping, name='test', user=user, format='CSV')  
        print errors
        self.assertEqual(len(errors), 2)
        self.assertEqual(Place.objects.all().count(), 210)
        
    def test_import_gpx(self):
        user=User.objects.get(username='admin')
        errors=implaces.import_places(GPX_FILE, None, name='test2', user=user, format='GPX')  
        print errors
        self.assertTrue(not errors )
        self.assertEqual(Place.objects.all().count(), 4)
        