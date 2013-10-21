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


from django.test.utils import setup_test_environment
setup_test_environment()

import logging
logging.basicConfig(level=logging.DEBUG)

CSV_FILE=os.path.join(os.path.split(__file__)[0], './pivovary.csv')
class ImportTest1(DjangoTestCase):
    def test_headers(self):
        headers, length, lines=implaces.extact_headers(CSV_FILE)
        print headers
        print length
        print lines
        self.assertTrue(len(headers)>5)
        self.assertEqual(len(headers), len(length))
        self.assertEqual(len(lines),5)
        
    
    def test_mapping(self):
        fields= implaces.get_mappable_fields()
        self.assertTrue(len(fields)>5)
        print fields
        
        
from myplaces.models import Place 
class ImportTest2(DjangoTestCase):
     
    def test_import(self):
        mapping= {u'url': 4, 'position': -4, u'name': 0, u'address': {u'unformatted': 1, u'phone': 5, u'email': 6}}
        errors=implaces.import_places(CSV_FILE, mapping, name='test')  
        self.assertEqual(len(errors), 2)
        self.assertEqual(Place.objects.all().count(), 210)
        