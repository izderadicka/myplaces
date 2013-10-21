'''
Created on Jul 30, 2013

@author: ivan

'''
import re
def norm_text(in_text):
    if not in_text:
        return None
    text=unicode(in_text).strip()
    if text:
        text=text.replace('\n',' ')
        text=text.replace('\r', '')
        text=text.replace('\t', ' ')
    return text.encode('utf-8')
        
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