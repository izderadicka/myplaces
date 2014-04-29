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
from geopy.exc import GeopyError as GeocoderError
import sys
import base64
logging.basicConfig(level=logging.DEBUG)
log=logging.getLogger('grabber.pivovary')

BASE='http://www.pivovary.info/'
gcoder=geocoders.GoogleV3()

def norm_text(in_text):
    text=unicode(in_text).strip()
    if text:
        text=text.replace('\n',' ')
        text=text.replace('\r', '')
        text=text.replace('\t', ' ')
    return text
        
def text_for_label(body, label):
    address_label=body.find('b',text=re.compile(r'\s*'+label+r'\s?:\s*',re.IGNORECASE))
    if not address_label:
        return
    next=address_label.next
    max_steps=100
    while max_steps:
        next=next.next
        max_steps-=1
        if isinstance(next, bs4.NavigableString):
            text=norm_text(next)
            if text:
                return text
                break
            
EMAIL_RE=re.compile(r'^[^@]+@[^@]+\.[^@]+$')
WWW_RE=re.compile(r'www\.[^.]+\.\w{1,6}', re.IGNORECASE)
PHONE_RE=re.compile(r'^(\+?[\s\d]+[,;]?)*$')
def parse_page(link):
    data={}
    page_url=BASE+link
    page=urllib2.urlopen(page_url).read()
    page=bs4.BeautifulSoup(page)
    head=page.find('td','otop')
    name=norm_text(u' '.join(head.strings))
    data['name']=name
    images=head.find_all('img')
    
    for n,i in enumerate(images):
        if n>=2:
            break
        img_url=urlparse.urljoin(page_url, i['src'])
        try:
            img_data=urllib2.urlopen(img_url).read()
            img_data=base64.b64encode(img_data)
        except urllib2.HTTPError, e:
            log.error('Errot when fetching logo image %s: %s', img_url, e)
        data['logo%d'%n]=img_data
       
        
    body=page.find('td','menu').find('td','vlevoleft')    
    address=text_for_label(body, 'adresa')
    if address:
        data['address']=address
        while address:
            
            try:
                
                places=gcoder.geocode(address, exactly_one=False, bounds="48.195387,11.028442|51.103522,19.356079")
                indx=0
                if not places:
                    log.error('Cannot get location for address %s', data['address'])
                    break
                if len(places)>1:
                    log.error('Returned more place then 1 - %d: %s', len(places), places)
                    ln=0
                    for i,p in enumerate(places):
                        if len(p[0])>ln:
                            indx=i
                            ln=len(p[0])
                
                place, (lat, lng)=places[indx]
                log.debug('Located to %s : %.5f %.5f', place, lat, lng)
                data['verified_address']=place
                data['location']=(lat, lng)
                break
            except GeocoderError:
                address_list=re.split(r'[,;]', address)
                if len(address_list)>=3:
                    address =','.join(address_list[1:])
                else:
                    log.error('Cannot get location for address %s', data['address'])
                    break
    else:
        log.error('Cannot get address for %s %s', name, page_url)
    phone=text_for_label(body, 'telefon')
    if phone: 
        m=PHONE_RE.match(phone)
        if m:
            data['phone']=phone
    email=text_for_label(body, 'e-mail')
    if email: 
        m=EMAIL_RE.match(email)
        if m:
            data['email']=email
    brewer=text_for_label(body, u'sládek')
    if brewer: data['brewer']=brewer      
    owner=text_for_label(body, u'vlastník')
    if owner: data['owner']=owner
    
    www=body.find(text=WWW_RE)
    if www:
        www=u'http://'+unicode(www).strip()
        try:
            urllib2.urlopen(www, timeout=15)
        except Exception, e:
            log.error('Cannot get url %s error %s',www,e)
            www=None
        else:
            data['url']=www
    
          
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
    page=urllib2.urlopen('http://www.pivovary.info/showpage.php?name=prehled').read()
   
    
    page=bs4.BeautifulSoup(page, "html.parser")
    blist=page.find_all('img', src="tecka.jpg")
    with open(args[0],'w') as f:
        writer=csv.DictWriter(f, ['name', 'address','verified_address', 'location','url', 'phone',
                                  'email','brewer', 'owner'], extrasaction='ignore')
        writer.writeheader()
        for i in blist:
            blink=i.find_next('a')
            log.debug("Processing link %s", blink['href'])
            try: 
                data=parse_page(blink['href'])
            except urllib2.HTTPError, e:
                log.error('Cannot get details for %s, error %s', blink['href'], e)
                continue
            log.debug(data)
            writer.writerow(data)
    
    
if __name__=='__main__':
    main()