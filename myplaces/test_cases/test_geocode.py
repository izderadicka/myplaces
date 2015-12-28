# -*- coding: utf-8 -*- 
'''
Created on Aug 21, 2013

@author: ivan
'''

import unittest
import os,re
from myplaces import geocode
from myplaces.models import Address
from django.contrib.gis.geos.point import Point
import csv

CSV_FILE=os.path.join(os.path.split(__file__)[0], './pivovary.csv')

class TestGeocode(unittest.TestCase):
    def test_geocode(self):
        
        pos,coords=geocode.get_coordinates(Address(unformatted=u'Hybešova 2, Praha 8, Česká republika'), True)
        self.assertTrue(pos is not None)
        print pos, coords
        
        pos,coords=geocode.get_coordinates(Address(unformatted=u'Čapkova 1848, 252 28 Černošice'), True)
        self.assertTrue(pos is not None)
        print pos, coords
        pos,coords=geocode.get_coordinates(Address(street='231 Baker Street', city='London',
                                postal_code='NW1 6XE', country='United Kingdom'), True)
        self.assertTrue(pos is not None)
        print pos, coords
        pos,coords=geocode.get_coordinates(Address(unformatted=u'Dolní Sklenov 33, 739 46 Hukvaldy; Hostinec U Zastávky'), True)
        self.assertTrue(pos is not None)
        print pos, coords
        
        
        
        
        
    def test_geocode2(self):
        
        pos,coords=geocode.get_coordinates(Address(unformatted=u'Čapkova 1848, 252 28 Černošice'))
        self.assertTrue(pos is not None)
        print pos, coords
        pos,coords=geocode.get_coordinates(Address(street='231 Baker Street', city='London',
                                postal_code='NW1 6XE', country='United Kingdom'))
        self.assertTrue(pos is not None)
        print pos, coords
        try:
            pos,coords=geocode.get_coordinates(Address(unformatted=u'Dolní Sklenov 33, 739 46 Hukvaldy; Hostinec U Zastávky'))
            self.fail("This address should  not be found by Nominatim")
        except geocode.NotFound:
            pass
        
    def test_geocode3(self):
        a=geocode.NominatimAddressAdapter(Address(street=u'Mezibranská 21', postal_code='110 00', city= 'Praha 1'))
        s=unicode(a)
        self.assertEqual(s, u'Mezibranská 21, Praha')
        
        #Tietgensgade 37, DK-1566 COPENHAGEN V,  DENMARK
        
        a=geocode.NominatimAddressAdapter(Address(street=u'Tietgensgade 37', postal_code='DK-1566', 
                                                  city= 'COPENHAGEN V', country='DENMARK'))
        s=unicode(a)
        self.assertEqual(s, u'Tietgensgade 37, COPENHAGEN, DENMARK')
        
        a=geocode.NominatimAddressAdapter(Address(unformatted=u'Čapkova 1848, 252 28 Černošice'))
        s=unicode(a)
        self.assertEqual(s, u'Čapkova 1848, Černošice')
        
        a=geocode.NominatimAddressAdapter(Address(unformatted=u'Krymská 38, Praha 10, Praha 10, Česká republika'))
        s=unicode(a)
        self.assertEqual(s, u'Krymská 38, Praha, Praha, Česká republika')
        
        a=geocode.NominatimAddressAdapter(Address(unformatted=u'Ke Kozím hřbetům 755/8, Praha 6 Suchdol, Česká republika'))
        s=unicode(a)
        self.assertEqual(s, u'Ke Kozím hřbetům 755/8, Praha Suchdol, Česká republika')
        
        
        
        a=geocode.NominatimAddressAdapter(Address(street=u'J.Wolkera 603', postal_code="250 01", city=u"Brandýs nad Labem"))
        s=unicode(a)
        self.assertEqual(s, u'Wolkera 603, Brandýs nad Labem')
        
        a=geocode.NominatimAddressAdapter(Address(unformatted=u'nám. Legií 851, 530 02 Pardubice'))
        s=unicode(a)
        self.assertEqual(s, u'Legií 851, Pardubice')
        
        
        
        a=geocode.NominatimAddressAdapter(Address(street=u'Komenského 48', postal_code="549 01", city=u"Nové Město n. Metují"))
        s=unicode(a)
        self.assertEqual(s, u'Komenského 48, Nové Město Metují')
#         pos,coords=geocode.get_coordinates(Address(unformatted=u'Čapkova 1848, 252 28 Černošice'))
#         self.assertTrue(pos is not None)
#         print pos, coords


    def test_geocode4(self):
        
        pos,coords=geocode.get_coordinates(Address(unformatted=u'Třebičská 342/10, 594 01 Velké Meziříčí'))
        self.assertTrue(pos is not None)
        print pos, coords
        
        pos,coords=geocode.get_coordinates(Address(unformatted=u'Želiv 1, 394 44'))
        self.assertTrue(pos is not None)
        print pos, coords
        
        pos, coords= geocode.get_coordinates(Address(city=u"Svojšice", country=u"Česko"))
        self.assertTrue(pos is not None)
        
        pos, coords= geocode.get_coordinates(Address(street=u"Líšno", country=u"Česko"))
        self.assertTrue(pos is not None)
        
        pos, coords= geocode.get_coordinates(Address(country=u"Česko"))
        self.assertTrue(pos is not None)
        
     
    samples=[(CSV_FILE, lambda l: Address(unformatted=l[1])),
             ('./unetice.csv', lambda l:Address(street=l[1], city=l[2], country=l[3])),
             ('./metoda mojzisove.csv', lambda l:Address(street=l[3], postal_code=l[4], city=l[5]))
             ]   
        
    def test_geocode_from_csv(self):
        if NO<0:
            return
        with file(self.samples[NO][0], 'rb') as f:
            reader=csv.reader(f, dialect=csv.excel)
            headers=reader.next()
            results=[]
            def fmt_loc(point):
                if not point:
                    return ''
                return'%.5f,%.5f'%(point[1], point[0])
            for i,l in enumerate(reader):
                address=self.samples[NO][1](l)
                if not unicode(address):
                    continue
                adr1,adr2,loc1,loc2=None, None, None, None
                try:
                    adr1,loc1=geocode.get_coordinates(address, False)                  
                except geocode.NotFound:
                    pass
                try:
                    adr2,loc2=geocode.get_coordinates(address, True)
                except geocode.NotFound:
                    pass
                
                
                d=None
                if loc1 and loc2:
                    d= loc1.transform(900913,True).distance(loc2.transform(900913,True))
                    
                if not loc1 or (d is not None and d>100):
                    results.append({'line':i, 'search_addr':address, 'nominatim_addr':adr1,
                                    'google_adr':adr2, 'nominatim_loc':fmt_loc(loc1),'google_loc':fmt_loc(loc2) ,'dist':d or -1})
                print i,address,'::',adr1,loc1,'|', adr2, loc2, '::', d 
                #if i>0: break
        with open('test_res.txt', 'w') as out:
            for r in results:
                ol= '%(line)d\t%(dist).0f\t%(search_addr)s\t%(nominatim_addr)s\t%(google_adr)s' %r
                print ol
                out.write(ol+'\n')
        out.close()
        print 'TOTAL ISSUES: ', len(results)
        
        
    def test_reverse(self):
            
        pos= '49.9506159,14.3155932'
        c= geocode.Google()
        adr, p=c.reverse(pos)
        print adr, p
        c= geocode.OSMNominatim()
        adr, p=c.reverse(pos)
        print adr, p
        point=Point(14.3155932, 49.9506159, srid=4326)
        adr2, p2=c.reverse(point)
        
        self.assertEqual(p,p2)
        self.assertTrue(adr2.street,adr.street)
        
        point2=point.transform(3857, True)
        
        adr3, p3=c.reverse(point2)
        
        self.assertEqual(p,p3)
        self.assertTrue(adr3.street,adr.street)
        
        
        adr, p=c.reverse('50.0027028,15.0414849')
        self.assertEqual(adr.postal_code, '28107')

NO=-1                  
if __name__=='__main__':
    NO=0 
    test='test_geocode2'
    import sys
    if len(sys.argv)>1:
        test=sys.argv[1]
    if len(sys.argv)>2:
        NO=int(sys.argv[2])
        
    sys.argv = ['', 'TestGeocode.'+test]
    unittest.main()
    