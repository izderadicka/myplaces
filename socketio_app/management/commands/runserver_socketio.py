
from re import match
from thread import start_new_thread
from time import sleep
from os import getpid, kill, environ
from signal import SIGINT

from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler
from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands.runserver import naiveip_re, DEFAULT_PORT
from django.utils.autoreload import code_changed, restart_with_reloader
from socketio.server import SocketIOServer
from optparse import make_option


import gevent.monkey
gevent.monkey.patch_all()
from psycogreen.gevent import patch_psycopg
patch_psycopg()

RELOAD = False

def reload_watcher():
    global RELOAD
    while True:
        RELOAD = code_changed()
        if RELOAD:
            kill(getpid(), SIGINT)
        sleep(1)

class Command(BaseCommand):
    
    option_list=BaseCommand.option_list + (
        make_option('--use_static_handler', action='store_true', help="Serves static files - only for debugging!"),
                                           )

    def handle(self, addrport="", *args, **options):

        if not addrport:
            self.addr = ''
            self.port = DEFAULT_PORT
        else:
            m = match(naiveip_re, addrport)
            if m is None:
                raise CommandError('"%s" is not a valid port number '
                                   'or address:port pair.' % addrport)
            self.addr, _, _, _, self.port = m.groups()

        # Make the port available here for the path:
        #   socketio_tags.socketio ->
        #   socketio_scripts.html ->
        #   io.Socket JS constructor
        # allowing the port to be set as the client-side default there.
        environ["DJANGO_SOCKETIO_PORT"] = str(self.port)
        if settings.DEBUG:
            start_new_thread(reload_watcher, ())
        try:
            bind = (self.addr, int(self.port))
            print
            print "SocketIOServer running on %s:%s" % bind
            print
            #inject this setting - needed to initialize zmq in 'green' mode
            settings._wrapped.USE_GEVENT=True
            handler = self.get_handler(*args, **options)
            server = SocketIOServer(bind, handler, resource="socket.io", policy_server=True)
            server.serve_forever()
        except KeyboardInterrupt:
            if RELOAD:
                server.stop()
                print "Reloading..."
                sleep(1)
                restart_with_reloader()
            else:
                raise

    def get_handler(self, *args, **options):
        """
        Returns the django.contrib.staticfiles handler.
        """
        handler = WSGIHandler()
        try:
            from django.contrib.staticfiles.handlers import StaticFilesHandler
        except ImportError:
            return handler
        use_static_handler = options.get('use_static_handler', True)
       
        if (settings.DEBUG or use_static_handler):
            handler = StaticFilesHandler(handler)
        return handler
