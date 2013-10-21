'''
Created on Jun 13, 2013

@author: ivan
'''

from django import template 

register=template.Library()


@register.filter
def getitem(value, key):
    return value.get(key)