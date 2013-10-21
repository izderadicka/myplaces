# Create your views here.
from django.shortcuts import render_to_response, redirect
import forms
from django.template.context import RequestContext
from django.utils.translation import ugettext as _
from django.views.generic import  ListView
from django.views.generic.edit import UpdateView
from django.contrib.gis.geos import Point

import logging
from django.http import HttpResponse, HttpResponseBadRequest,\
    HttpResponseNotFound
import sys
import os
import json
from myplaces.models import PlacesGroup, Place
from myplaces.voronoi import voronoi2
log=logging.getLogger('mp.views')
from django.views.decorators.csrf import csrf_exempt

import implaces
import utils
import remote

from sockets import ctx as zmq_ctx

def rr(request, template, ctx):
    return render_to_response(template, ctx, context_instance=RequestContext(request))
def rjson(ctx):
    return HttpResponse(json.dumps(ctx), mimetype="application/json")


def upload_places(request, step):
    
    step=int(step)
    if step==1:
        if request.method=='GET':
            form=forms.ImportForm(initial={'call_id':utils.gen_uid()})
        elif request.method=='POST':
            form=forms.ImportForm(request.POST, request.FILES)
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
    headers, max_lens, sample_lines=implaces.extact_headers(tmp_file)
    return rr(request, 'upload2.html', {'headers':headers, 'max_lens': max_lens, 
										'sample_lines':sample_lines, 'step':step,
										'step_1':utils.serialize(form),
                                        'stream_id': tmp_file,
										'mappable_fields':implaces.get_mappable_fields(),
                                        'values':{}, 
                                         })
      
def _upload_places_fin(request, step):
    form=utils.deserialize(request.POST.get('step_1'))
    mapping, values, errors =implaces.extract_mapping(request.POST)
        
    if errors: 
        return rjson({'errors':errors})
    tmp_file=form.get('csv_file')
    del form['csv_file']
    socket=None
    try:
        socket=remote.create_socket(zmq_ctx, 'client', 0)
        try:
            remote.call_remote(socket, 'import_places', [tmp_file, tmp_file, mapping, form.get('name'), 
                     form.get('description'), form.get('private'), 
                     request.user], call_id=form.get('call_id'))
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
    try:
        group=PlacesGroup.objects.get(id=group_id)
    except PlacesGroup.DoesNotExist:
        return HttpResponseNotFound('Non existent group id')
    
    if group.places.all().count()>=3:
        q=group.places.all().transform(srid=3857)
        points= [(p.position.x, p.position.y) for p in  q]
        
        bbox=q.extent()
        xsize=(bbox[2]-bbox[0])/3.0
        ysize=(bbox[3]-bbox[1])/3.0
        bbox=(bbox[0]-xsize, bbox[1]-ysize, bbox[2]+xsize, bbox[3]+ysize)
        bbox2=(Point(bbox[0], bbox[1], srid=4326).transform(3857, True),
              Point(bbox[2], bbox[3], srid=4326).transform(3857, True))
        bbox2=(bbox2[0][0], bbox2[0][1], bbox2[1][0], bbox2[1][1])
       
        lines=voronoi2(points, bbox2)
        lines=map(lambda p: (Point(*p[0], srid=3857).transform(4326, True), 
                             Point(*p[1], srid=3857).transform(4326, True)), lines)
        
        result={"type":"FeatureCollection",
                'features':[
                { 'type':'Feature',
                 'geometry':{'type':'MultiLineString', 'coordinates':[[list(l[0]), list(l[1])] for l in lines]}},
                {'type':'Feature',
                 'geometry':{'type': 'Polygon', 'coordinates': [[[bbox[0], bbox[1]], [bbox[2], bbox[1]], 
                                                                [bbox[2], bbox[3]], [bbox[0], bbox[3]],
                                                                [bbox[0], bbox[1]]]]}}
                ],
                'properties':{'bbox':list(bbox)}
                }
    else:
        result={"type":"FeatureCollection",
                "features":[]}
            
    return HttpResponse(json.dumps(result), mimetype='application/json')

class ExtUpdateView(UpdateView):
    #We would like to display same form - with 
    def form_valid(self, form):
        self.object = form.save(user=self.request.user)
        return self.render_to_response(self.get_context_data(form=form, success=True))
    
    

    