from django.conf.urls.defaults import patterns, include, url

from django.conf.urls.defaults import *
from django.contrib.gis import admin
import myplaces.urls
import myplaces.remote as remote
from django.conf import settings
from django.views.generic import RedirectView
from account import AuthenticationLockForm
import socketio.sdjango


#patch site login form
admin.site.login_form=AuthenticationLockForm
admin.autodiscover()


#Init zmq for remote calls 
remote.init(hasattr(settings,'USE_GEVENT') and settings.USE_GEVENT)
socketio.sdjango.autodiscover()


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mapy.views.home', name='home'),
    # url(r'^mapy/', include('mapy.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    #Uncomment the next line to enable the admin:
    url(r'^/?$', RedirectView.as_view(url='/mp/')),
    url(r'^admin/', include(admin.site.urls)),
    # This one enables site wise websocket 
    url("^socket\.io", include(socketio.sdjango.urls)),
    # this is js local strings catalogue
    url(r'^js-locale/(?P<packages>\S+?)/?$', 'django.views.i18n.javascript_catalog'),
    url(r'^mp/', include(myplaces.urls)),
    (r'^accounts/', include('account')),
    url(r'^captcha/', include('captcha.urls')),
    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),
)
