# -*- coding: utf-8 -*- 
'''
Created on Aug 21, 2013

@author: ivan
'''

from myplaces.models import *
from django import test
import sys
from django.contrib.auth.models import User

class TestModels(test.TestCase):
    
    fixtures=['test_data_auth.json']
    
    def test_address(self):
        a1=Address(street="Čamrdova 25", city="Kůlice", postal_code="789 00", country="Česká Republika")
        self.assertTrue(isinstance(unicode(a1), unicode))
        self.assertTrue(len(unicode(a1))>15)
        self.assertTrue(str(a1))
        
        
        a2=Address(unformatted='Marakova 5, 111 00 Makakov, Gibonie')
        self.assertTrue(str(a2))
        
        
    def test_create(self):
        grp=PlacesGroup(name="Unit Testing", description="ěščřžýáíéúů", private=True)
        grp.save(user='admin')
        adr=Address(street="Čamrdova 25", city="Kůlice", postal_code="789 00", country="Česká Republika")
        adr.save()
        place= Place(name="One place", description="Some text", position="POINT (14 50)", 
                     url="http://somewhere.com", address=adr, group=grp)
        place.save(user='admin')
        u=User.objects.get(username='admin')
        self.assertTrue(place.created_by == u)
        



        