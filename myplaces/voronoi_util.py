'''
Created on Nov 26, 2013

@author: ivan
'''

import remote
from django.conf import settings

def voronoi_remote(group_id, context=None):
    ctx=context or remote.context()   
    socket=ctx.socket(remote.zmq.REQ)  # @UndefinedVariable
    try:
        socket.connect(settings.REMOTE_ADDR_CALC)
        json= remote.call_remote(socket, 'calc_voronoi', (group_id,),  timeout=60)
    finally:
        socket.close()
    return json


        


