'''
Created on Jun 13, 2013

@author: ivan
'''

from django import template 
from django.template.base import VariableDoesNotExist
from django.core.urlresolvers import reverse
from django.conf import settings
import urllib

register=template.Library()


@register.filter
def getitem(value, key):
    return value.get(key)


@register.simple_tag(takes_context=True)        
def full_url(context, url_ref, secure=None, encode=None):
        req=context.get('request')
        if not req:
            raise VariableDoesNotExist('full_url tag requires request in the template context!')
        scheme='http://'
        if secure: # and not settings.DEBUG:
            scheme='https://'
        server=req.META.get('HTTP_HOST', '')
        url=scheme+server+reverse(url_ref)
        if encode:
            url=urllib.quote(url)
        return url
    
@register.simple_tag(takes_context=True)
def proto(context):
    req=context.get('request')
    if req and req.is_secure():
        return 'https'
    else:
        return 'http'