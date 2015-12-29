'''
Created on Dec 29, 2015

@author: ivan
'''
from voronoi import voronoi2
from models import PlacesGroup
import remote
from django.contrib.gis.geos import Point
import numpy
import json


def to_list(lines):
    result=[]
    def check_invalid(p):
        if len(p)!=2:
            return True
        for v in p:
            if v is None or not numpy.isfinite(v):
                return True
                
    for l in lines:
        if check_invalid(l[0]) or check_invalid(l[1]):
            continue
        result.append([list(l[0]), list(l[1])])
    return result

@remote.is_remote
def calc_voronoi(group_id):
    
    try:
        group=PlacesGroup.objects.get(id=group_id)
    except PlacesGroup.DoesNotExist:
        raise ValueError('Non existent group id')
    
    if group.places.all().count()>=3:
        q=group.places.all().transform(srid=3857)
        points= [(p.position.x, p.position.y) for p in  q]
#         xlim, ylim=20037508.3427, 15538711.096
#         bbox=q.extent()
#         xsize=(bbox[2]-bbox[0])/3.0
#         ysize=(bbox[3]-bbox[1])/3.0
#         xmin,ymin, xmax, ymax=bbox[0]-xsize, bbox[1]-ysize, bbox[2]+xsize, bbox[3]+ysize
#         bbox=(xmin if xmin>-180 else -180,ymin if ymin>-90 else -90, 
#              xmax if xmax<180 else 180, ymax if ymax<90 else 90)
        bbox=(-179.99, -80, 179.99,80)
        bbox2=(Point(bbox[0], bbox[1], srid=4326).transform(3857, True),
              Point(bbox[2], bbox[3], srid=4326).transform(3857, True))
        bbox2=(bbox2[0][0], bbox2[0][1], bbox2[1][0], bbox2[1][1])
        lines=voronoi2(points, bbox2)
            
        lines=map(lambda p: (Point(*p[0], srid=3857).transform(4326, True),
                             Point(*p[1], srid=3857).transform(4326, True)), lines)
        
        result={"type":"FeatureCollection",
                'features':[
                { 'type':'Feature',
                 'geometry':{'type':'MultiLineString', 'coordinates':to_list(lines)}},
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