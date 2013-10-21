# -*- coding: utf-8 -*- 
'''
Created on May 17, 2013

@author: ivan
'''

import urllib2
import urlparse
import bs4
import re
import logging
import optparse
import csv
from geopy import geocoders 
from geopy.geocoders.base import GeocoderError
import sys
import base64
logging.basicConfig(level=logging.DEBUG)
log=logging.getLogger('grabber.pivovary')

BASE='http://www.unetickypivovar.cz'
gcoder=geocoders.GoogleV3()

from utils import norm_text



def parse_page(link):
    def nt(elem, name):
        if elem:
            data[name]=norm_text(elem.text)
    data={}
    page_url=BASE+link
    page=urllib2.urlopen(page_url).read()
    page=bs4.BeautifulSoup(page)
    adr=page.find('div', 'location')
   
    nt(adr.find('div', 'street-address'), 'address_street')
    nt(adr.find('span', 'locality'),'address_city')
    nt(adr.find('div', 'country-name'), 'address_country')
    
    
    link=page.find('div', 'node-type-hospoda').find('a', text=re.compile('zde'))
    if link:
        data['url']= link['href']
        
    comment=page.find('div', 'node-type-hospoda').find('div', dir='ltr')
    if comment:
        comment=comment.text.replace(u'Více informací naleznete zde.', '')
        data['description']=norm_text(comment)
        
    coordinates=page.find('span', 'geo')
    if coordinates:
        data['location']=coordinates.find('abbr', 'latitude')['title']+', '+\
        coordinates.find('abbr', 'longitude')['title']
        
          
    return data

    


def main():
    parser=optparse.OptionParser('%s [options] file.cs')
    parser.add_option('-l', '--log', help='logfile')
    opts, args=parser.parse_args()
    if len(args)<1:
        parser.print_usage();
        sys.exit(1)
    if opts.log:
        h=logging.FileHandler(opts.log)
        h.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(message)s'))
        log.addHandler(h)
    page=urllib2.urlopen(BASE+'/kde-se-cepuje').read()
   
    
    page=bs4.BeautifulSoup(page, "html.parser")
    rows=page.find('div', id="content-area").table.find_all('tr')
    
    with open(args[0],'w') as f:
        writer=csv.DictWriter(f, ['name', 'address_street', 'address_city', 'address_country', 'location','url', 'description'], extrasaction='ignore')
        writer.writeheader()
        for row in rows[1:]:
            name=row.td.a
            
            data={'name':norm_text(name.text)}
            link=name['href']
            data.update(parse_page(link))
            log.debug(data)
            writer.writerow(data)
    
    
if __name__=='__main__':
    main()