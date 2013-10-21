'''
Created on Jun 13, 2013

@author: ivan
'''
from django.utils.translation import ugettext as _
from django import template

register=template.Library()

@register.tag
def headers_mapping(parser, token):
    args=token.split_contents()
    return HeadersMapping(*args)

class HeadersMapping(template.Node):
    def __init__(self, *args):
        self.args=args
        
    def render(self, context):
        pieces=[]
        for i,header in enumerate(context['headers']):
            pieces.append(u'<td><select name="mapping_%d" title="%s">' % (i, _('Select field to load to')))
            pieces.append(u'<option value=""></option>')
            for val, name in context['mappable_fields']:
                selected=''
                if  context.get('values') and context['values'].get(i)==val:
                    selected=u' selected'
                pieces.append(u'<option value="%s"%s>%s</option>'%(val, selected, name))
            pieces.append(u'</select></td>')
        return u'\n'.join(pieces)
            