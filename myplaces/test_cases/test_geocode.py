# -*- coding: utf-8 -*- 
'''
Created on Aug 21, 2013

@author: ivan
'''

import unittest
import os,re
from myplaces import geocode
from myplaces.models import Address
from myplaces.implaces import UnicodeReader

CSV_FILE=os.path.join(os.path.split(__file__)[0], './pivovary.csv')

class TestGeocode(unittest.TestCase):
    def test_gecode(self):
        
        pos,coords=geocode.get_coordinates(Address(unformatted=u'Čapkova 1848, 252 28 Černošice'))
        self.assertTrue(pos is not None)
        print pos, coords
        pos,coords=geocode.get_coordinates(Address(street='231 Baker Street', city='London',
                                postal_code='NW1 6XE', country='United Kingdom'))
        self.assertTrue(pos is not None)
        print pos, coords
        pos,coords=geocode.get_coordinates(Address(unformatted=u'Dolní Sklenov 33, 739 46 Hukvaldy; Hostinec U Zastávky'))
        self.assertTrue(pos is not None)
        print pos, coords
        
    def test_gecode2(self):
        
        pos,coords=geocode.get_coordinates(Address(unformatted=u'Čapkova 1848, 252 28 Černošice'),True)
        self.assertTrue(pos is not None)
        print pos, coords
        pos,coords=geocode.get_coordinates(Address(street='231 Baker Street', city='London',
                                postal_code='NW1 6XE', country='United Kingdom'), True)
        self.assertTrue(pos is not None)
        print pos, coords
        try:
            pos,coords=geocode.get_coordinates(Address(unformatted=u'Dolní Sklenov 33, 739 46 Hukvaldy; Hostinec U Zastávky'), True)
            self.fail("This address should  not be found by Nominatim")
        except geocode.NotFound:
            pass
        
        print pos, coords
        
        
    def no_test_geocode_from_csv(self):
        with file(CSV_FILE, 'rb') as f:
            reader=UnicodeReader(f)
            headers=reader.next()
            
            for i,l in enumerate(reader):
                address=l[1]
                m=re.search(r';\s+\d{3} \d{2}', address)
                if m:
                    address=map(lambda x:x.strip(),address.split(';'))
                    first=address[0]
                    del address[0]
                    address.append(first)
                    address=u', '.join(address)
                adr1,loc1,adr2,loc2=[None]*4
                try:
                    adr1,loc1=geocode.get_coordinates(Address(unformatted=address), False)                  
                except geocode.NotFound:
                    pass
                try:
                    adr2,loc2=geocode.get_coordinates(Address(unformatted=address), True)
                except geocode.NotFound:
                    pass
                
                print i,address,'::',adr1,loc1,'|', adr2, loc2
                if loc1 and loc2:
                    print 'Distance:', loc1.transform(900913,True).distance(loc2.transform(900913,True))
    