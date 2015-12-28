'''
Created on Dec 16, 2013

@author: ivan
'''


from resources import PlacesSearchMixin
from django.views.generic.base import View
from myplaces.models import Place, PlacesGroup
from django.http import Http404, HttpResponse
import format

class ExportView( View, PlacesSearchMixin):
    
    
    def get(self, request,  group, fmt, **kwargs):
        # this is to adapt to rest_framework, which expect QUERY_PARAMS attribute
        request.QUERY_PARAMS=request.GET
        self.queryset=Place.objects.all().filter(group=group)
        self.object_list = self.get_queryset()
        try:
            group=PlacesGroup.objects.get(id=group)
        except PlacesGroup.DoesNotExist:
            raise Http404('Invalid group id')
        ordering=request.QUERY_PARAMS.get('ordering')
        if ordering:
            self.object_list=self.object_list.order_by(ordering)
        
        if len(self.object_list) == 0:
            raise Http404(_(u"No data to export"))
        resp=self.prepare_response(fmt, group)
        
        return resp
    
    def prepare_response(self, fmt, group):
        try:
            fmt=format.get_fmt_descriptor(fmt)
        except KeyError:
            raise Http404('Invalid format name')
        response=HttpResponse(content_type=fmt.mime)
        fname=group.name.encode('utf-8') + ('.'+fmt.extensions[0] if fmt.extensions else '')
        response['Content-Disposition']= 'attachment; filename="%s"'%fname
        adapter=fmt.export_adapter
        if not adapter:
            raise Http404('This format does not support export')
        adapter(response).export(group, self.object_list)
        return response
    