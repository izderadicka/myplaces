'''
Created on Jun 19, 2013

@author: ivan
'''

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import myplaces.remote as remote
import myplaces.implaces as implaces
import os, threading
from django.utils.translation import ugettext as _
import logging
from optparse import make_option
import zmq
import time
from myplaces.voronoi_util import calc_voronoi #must import to register remote method



@remote.is_remote
def import_places(stream_id, temp_file, extra_params, name, description, 
                  private,  user,  existing='update', format='CSV', encoding='utf-8'):
    ctx=remote.context(True)
    pub_socket=remote.create_socket(ctx, 'pub')
    def report_error(line,msg):
        remote.send_msg(pub_socket, stream_id, 'error', {'line':line, 'msg':msg})
    def report_progress(line, total):
        remote.send_msg(pub_socket, stream_id, 'progress', {'line':line, 'total':total})
        
    try:    
        implaces.import_places(temp_file, extra_params, name, description, private, user, existing, encoding,  
                               report_error, report_progress, context=ctx, format=format)
        remote.send_msg(pub_socket, stream_id, 'done', '')
    finally:
        pub_socket.close()
        
        
class Thread(threading.Thread):  
    def __init__(self, ctx, *args, **kwargs):
        super(Thread, self).__init__(*args, **kwargs)
        self.setDaemon(True)
        self.context=ctx 
        
class GeocoderThread(Thread):
    def run(self):
        socket=self.context.socket(zmq.REP)
        socket.bind(settings.REMOTE_ADDR_GEOCODE)
        timer={'next_run':time.time()}
        while True:
            remote.do_remote_call(socket, False, allowed_methods=['geocode_remote'], 
                                  extra_kwargs={'timer':timer})
            


class CalcThread(Thread):
    def run(self):
        socket=self.context.socket(zmq.REP)
        socket.bind(settings.REMOTE_ADDR_CALC)
        while True:
            remote.do_remote_call(socket, False, ['calc_voronoi'])
            
class ImportThread(Thread):
    def run(self):
        in_socket=remote.create_socket(self.context, 'server')
        while True:
            remote.do_remote_call(in_socket)
        
    
            
        
class Command(BaseCommand):
    option_list=BaseCommand.option_list + \
    (make_option("-d", "--debug",  help="Switch on debug messaging" , action="store_true"),
     make_option("--test", help="Connects to test database", action="store_true"))
    
    def handle(self, *args, **options ):
        if options.get('debug'):
            logging.basicConfig(level=logging.DEBUG)
            logging.getLogger().setLevel(logging.DEBUG)
        if options.get('test') :
            from django.db import connections, DEFAULT_DB_ALIAS
            conn=connections[DEFAULT_DB_ALIAS]
            conn.settings_dict['NAME'] = 'test_'+conn.settings_dict['NAME']
            
               
            
        remote.init()
        ctx=remote.context(True)
        remote.run_proxy( ctx)
        workers=(GeocoderThread, ImportThread, CalcThread)
        for wc in workers:
            wc(ctx).start()
        
        while True:
            time.sleep(60)
       
       