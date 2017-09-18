#!/usr/bin/env python

import gevent.monkey
gevent.monkey.patch_all()
from psycogreen.gevent import patch_psycopg
patch_psycopg()

from re import match
import os.path,sys
sys.path.append(os.path.split(__file__)[0])
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

import django
from django.conf import settings
#settings.ROOT_URLCONF = 'sioroot'

from django.core.handlers.wsgi import WSGIHandler
from django.core.management.commands.runserver import naiveip_re
from socketio.server import SocketIOServer
from  argparse import ArgumentParser



def parse_args():
    p=ArgumentParser()
    p.add_argument('adr_and_port', default='', nargs='?', help='Serve on this address and port')
    p.add_argument('--use-static-handler', action='store_true', help="Serves static files - only for debugging!")
    opts=p.parse_args()
    return opts.adr_and_port, opts

def run(addrport, opts):
    if not addrport:
        addr = ''
        port = settings.SIO_PORT
    else:
        m = match(naiveip_re, addrport)
        if m is None:
            raise Exception('"%s" is not a valid port number '
                               'or address:port pair.' % addrport)
        addr, _, _, _, port = m.groups()

    # Make the port available here for the path:
    #   socketio_tags.socketio ->
    #   socketio_scripts.html ->
    #   io.Socket JS constructor
    # allowing the port to be set as the client-side default there.
    os.environ["DJANGO_SOCKETIO_PORT"] = str(port)
    django.setup()
    try:
        bind = (addr, int(port))
        print
        print "SocketIOServer running on %s:%s" % bind
        print
        #inject this setting - needed to initialize zmq in 'green' mode
        settings._wrapped.USE_GEVENT=True
        handler = get_handler(static=opts.use_static_handler)
        server = SocketIOServer(bind, handler, resource="socket.io", policy_server=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass

def get_handler(static=False):
    """
    Returns the django.contrib.staticfiles handler.
    """
    handler = WSGIHandler()
    try:
        from django.contrib.staticfiles.handlers import StaticFilesHandler
    except ImportError:
        return handler
    
   
    if (settings.DEBUG or static):
        handler = StaticFilesHandler(handler)
    return handler

if __name__=='__main__':
    run(*parse_args())