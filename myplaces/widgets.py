'''
Created on Oct 18, 2013

@author: ivan
'''
from __future__ import unicode_literals
from rest2backbone.widgets import DynamicWidget, DynamicRelatedWidget
from django.forms.util import flatatt
from django.utils.safestring import mark_safe

class LocationWidget(DynamicWidget):
    js_widget='customWidgets.Location'
    def render_template(self, name, attrs, field):
        final_attrs = self.build_attrs(attrs)
        output=['<div%s>'% flatatt(final_attrs)]
        output.append(u'<input type="text" name="%(name)s" value="<%%= %(name)s%%>">' % {'name':name})
        output.append('<div class="map_btn small_btn"></div>')
        output.append('</div>')
        return mark_safe('\n'.join(output))
    
    def js_options(self, name, attrs, field):
        return {'name':name}
    

        
        
        
        
        