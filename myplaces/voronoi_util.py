'''
Created on Nov 26, 2013

@author: ivan
'''

from voronoi import voronoi2
from models import PlacesGroup
import json
from django.contrib.gis.geos import Point
import remote
from django.conf import settings

def voronoi_remote(group_id, context=None):
    ctx=context or remote.context()   
    socket=ctx.socket(remote.zmq.REQ)  # @UndefinedVariable
    socket.connect(settings.REMOTE_ADDR_CALC)
    
    json= remote.call_remote(socket, 'calc_voronoi', (group_id,),  timeout=60)
    
    return json

@remote.is_remote
def calc_voronoi(group_id):
    
    try:
        group=PlacesGroup.objects.get(id=group_id)
    except PlacesGroup.DoesNotExist:
        raise ValueError('Non existent group id')
    
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
        
    return json.dumps(result)
