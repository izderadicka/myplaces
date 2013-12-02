# Create your views here.
from django.shortcuts import render_to_response, redirect
import forms
from django.template.context import RequestContext
from django.utils.translation import ugettext as _
from django.views.generic.edit import UpdateView

import logging
from django.http import HttpResponse, HttpResponseBadRequest,\
    HttpResponseNotFound
import sys
import os
import json
from myplaces.models import PlacesGroup, Place
from myplaces.voronoi_util import voronoi_remote
log=logging.getLogger('mp.views')
import django_mobile
import implaces
import utils
import remote


def rr(request, template, ctx):
    return render_to_response(template, ctx, context_instance=RequestContext(request))
def rjson(ctx):
    return HttpResponse(json.dumps(ctx), mimetype="application/json")

def upload_places(request, step):
    flavour=django_mobile.get_flavour(request, 'full')
    if flavour!='full':
        return HttpResponse('Import is designed to work only in full browser, not mobile', 'text/plain', 400)
    step=int(step)
    if step==1:
        if request.method=='GET':
            form=forms.ImportForm(initial={'call_id':utils.gen_uid()})
        elif request.method=='POST':
            form=forms.ImportForm(request.POST, request.FILES, user=request.user)
            if form.is_valid():
                return _upload_places_2(request, step+1, form)
        return rr(request, 'upload1.html', {'form':form, 'step':step})
    elif step==2 and request.method=='POST':
        return _upload_places_fin(request,step)
        
def _upload_places_2(request,step, form):   
    tmp_file=implaces.save_file(form.cleaned_data.get('csv_file'))
    log.debug('CSV temporary file %s',tmp_file)
    form=form.cleaned_data
    form['csv_file']=tmp_file 
    group_exists=PlacesGroup.objects.filter(name=form['name']).count()
    headers, max_lens, sample_lines=implaces.extact_headers(tmp_file)
    return rr(request, 'upload2.html', {'headers':headers, 'max_lens': max_lens, 
										'sample_lines':sample_lines, 'step':step,
										'step_1':utils.serialize(form),
                                        'stream_id': tmp_file,
										'mappable_fields':implaces.get_mappable_fields(),
                                        'values':{}, 
                                        'group_exists':group_exists
                                         })
      
def _upload_places_fin(request, step):
    form=utils.deserialize(request.POST.get('step_1'))
    existing=request.POST.get('update_type') or 'skip'
    mapping, values, errors =implaces.extract_mapping(request.POST)
        
    if errors: 
        return rjson({'errors':errors})
    tmp_file=form.get('csv_file')
    del form['csv_file']
    socket=None
    zmq_ctx=remote.context()
    try:
        socket=remote.create_socket(zmq_ctx, 'client', 0)
        try:
            remote.call_remote(socket, 'import_places', [tmp_file, tmp_file, mapping, form.get('name'), 
                     form.get('description'), form.get('private'), 
                     request.user, existing], call_id=form.get('call_id'))
        except remote.RemoteError, e:
            return rjson({'errors':[_('Remote Error (%s)')% str(e)]})
    finally:
        if socket:
            socket.close()
    #errors=implaces.import_places(tmp_file, mapping, user=request.user, **form)
    
    
    return rjson({})



def group_geojson(request, group_id):
    try:
        group=PlacesGroup.objects.get(id=group_id)
    except PlacesGroup.DoesNotExist:
        return HttpResponseNotFound('Non existent group id')
    
    return HttpResponse(group.as_geojson(), mimetype='application/json')



    

def group_voronoi_geojson(request, group_id):
    json_data=voronoi_remote(group_id)
            
    return HttpResponse(json_data, mimetype='application/json')

class ExtUpdateView(UpdateView):
    #We would like to display same form - with 
    def form_valid(self, form):
        self.object = form.save(user=self.request.user)
        return self.render_to_response(self.get_context_data(form=form, success=True))
    
    

    