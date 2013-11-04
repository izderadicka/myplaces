# coding=utf-8
'''
Created on Oct 28, 2013

@author: ivan
'''
import unittest
import myplaces.remote as remote
from myplaces.models import Address
import myplaces.geocode as geo
import threading
import Queue
import sys
import unicodedata
from django.contrib.gis.geos.point import Point
import subprocess
import os


class Worker(threading.Thread):
    def __init__(self, q, res, alt=False):
        self.q=q
        self.r=res
        super(Worker, self).__init__()
        self.setDaemon(True)
        self.alt=alt
    def run(self):
        while True:
            try:
                a=self.q.get(False)
                try:
                    res=geo.get_coordinates_remote(a, self.alt) 
                    self.r.append((res,a))
                finally:
                    self.q.task_done()
            except Queue.Empty:
                break


nd_charmap = {
        u'\N{Latin capital letter AE}': 'AE',
        u'\N{Latin small letter ae}': 'ae',
        u'\N{Latin capital letter Eth}': 'D', #
        u'\N{Latin small letter eth}': 'd', #
        u'\N{Latin capital letter O with stroke}': 'O', #
        u'\N{Latin small letter o with stroke}': 'o',  #
        u'\N{Latin capital letter Thorn}': 'Th',
        u'\N{Latin small letter thorn}': 'th',
        u'\N{Latin small letter sharp s}': 's',#
        u'\N{Latin capital letter D with stroke}': 'D',#
        u'\N{Latin small letter d with stroke}': 'd',#
        u'\N{Latin capital letter H with stroke}': 'H',
        u'\N{Latin small letter h with stroke}': 'h',
        u'\N{Latin small letter dotless i}': 'i',
        u'\N{Latin small letter kra}': 'k',#
        u'\N{Latin capital letter L with stroke}': 'L',
        u'\N{Latin small letter l with stroke}': 'l',
        u'\N{Latin capital letter Eng}': 'N', #
        u'\N{Latin small letter eng}': 'n', #
        u'\N{Latin capital ligature OE}': 'Oe',
        u'\N{Latin small ligature oe}': 'oe',
        u'\N{Latin capital letter T with stroke}': 'T', #
        u'\N{Latin small letter t with stroke}': 't',#
    }

def remove_dia(text):
    "Removes diacritics from the string"
    if not text:
        return text
    uni = None
    if isinstance(text, unicode):
        uni = text
    else :
        encoding=sys.getfilesystemencoding()
        uni =unicode(text, encoding, 'ignore')
    s = unicodedata.normalize('NFKD', uni)
    b=[]
    for ch in s:
        if  unicodedata.category(ch)!= 'Mn':
            if nd_charmap.has_key(ch):
                b.append(nd_charmap[ch])
            elif ord(ch)<128:
                b.append(ch)
            else:
                b.append(' ')
    return ''.join(b)
            
            
addresses=[u'U nemocnice 1, 690 74 Břeclav',
           u'Čapkova 1848, 252 28 Černošice',
           u'Viniční 235, 628 00 Brno', 
           u'Ke Kozím hřbetům 755/8, Praha Suchdol, Česká republika',
           u'nám. Legií 851, 530 02 Pardubice']        

class TestGeoRemote(unittest.TestCase):
    
    def setUp(self):
        remote.init()
        manage=os.path.join(os.path.split(__file__)[0], '../../manage.py')
        self.p=subprocess.Popen(['python', manage,  'process_server'], shell=False)
    
        
    def tearDown(self):
        self.p.kill()
        

    def test_remote(self):
        a=Address(unformatted=u"nám. Legií 851, 530 02 Pardubice")
        adr, pos=geo.get_coordinates_remote(a)
        self.assertTrue(adr.city, 'Pardubice')
        print pos
        
    def test_reverse(self):   
        pos= '49.9506159,14.3155932'
        adr, pos = geo.get_address_remote(pos)
        self.assertEqual(adr.city, u'Černošice')
        pos=Point(14.3155932, 49.9506159, srid=4326)
        adr, pos = geo.get_address_remote(pos)
        self.assertEqual(adr.city, u'Černošice')
        pos=Point(14.4179732,50.0879913, srid=4326)
        adr, pos = geo.get_address_remote(pos)
        print adr
        self.assertTrue(adr.street.find(u'Kaprova')>-1)
        
        
    def test_concurrent(self):
        
        res=[]
        q=Queue.Queue()
        for i in range(4):
            for a in addresses:
                q.put(a)
                
        workers=[]
        for i in range(3):
            w=Worker(q, res)
            w.start()
            workers.append(w)
        
        q.join()
        
        self.assertEqual(len(res), 20)
        
        for na, a in res:
            print na[0],'===', a
            self.assertTrue(remove_dia(na[0].city.lower()) in remove_dia(a.lower()))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()