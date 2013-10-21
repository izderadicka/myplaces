from django.conf.urls.defaults import patterns, include, url

from django.conf.urls.defaults import *
from django.contrib.gis import admin
import myplaces.urls

import socketio.sdjango



admin.autodiscover()
socketio.sdjango.autodiscover()


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mapy.views.home', name='home'),
    # url(r'^mapy/', include('mapy.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    #Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    # This one enables site wise websocket 
    url("^socket\.io", include(socketio.sdjango.urls)),
    # this is js local strings catalogue
    url(r'^js-locale/(?P<packages>\S+?)/?$', 'django.views.i18n.javascript_catalog'),
    url(r'^mp/', include(myplaces.urls)),
    (r'^login/$', 'django.contrib.auth.views.login', {'template_name':'login.html'}),
    (r'^logout/$', 'django.contrib.auth.views.logout'),
     url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),
#    url("^chat/", include("chat.urls")),
)
