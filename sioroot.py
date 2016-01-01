from django.conf.urls import patterns, include, url

import myplaces.remote as remote
from  socketio_app import sdjango



#Init zmq for remote calls 
remote.init(True)
sdjango.autodiscover()


urlpatterns = patterns('',
    
   
    # This one enables site wise websocket 
    url("^socket\.io", include(sdjango.urls)),
    
)
