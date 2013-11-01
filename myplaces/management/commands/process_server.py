'''
Created on Jun 19, 2013

@author: ivan
'''

from django.core.management.base import BaseCommand, CommandError
import myplaces.remote as remote
import myplaces.implaces as implaces
import os, threading
from django.utils.translation import ugettext as _
import logging
from optparse import make_option
import zmq
import time



@remote.is_remote
def import_places(stream_id, temp_file, mapping, name, description, 
                  private,  user,  existing='update', encoding='utf-8'):
    ctx=remote.context(True)
    pub_socket=remote.create_socket(ctx, 'pub')
    def report_error(line,msg):
        remote.send_msg(pub_socket, stream_id, 'error', {'line':line, 'msg':msg})
    def report_progress(line, total):
        remote.send_msg(pub_socket, stream_id, 'progress', {'line':line, 'total':total})
        
    try:    
        implaces.import_places(temp_file, mapping, name, description, private, user, existing, encoding,  
                               report_error, report_progress, context=ctx)
        remote.send_msg(pub_socket, stream_id, 'done', '')
    finally:
        pub_socket.close()
        
        
class Thread(threading.Thread):  
    def __init__(self, ctx, *args, **kwargs):
        super(Thread, self).__init__(*args, **kwargs)
        self.setDaemon(True)
        self.context=ctx 
        

GC_ADDR='tcp://127.0.0.1:10009'         
class GeocoderThread(Thread):
    def run(self):
        socket=self.context.socket(zmq.REP)
        socket.bind(GC_ADDR)
        timer={'next_run':time.time()}
        while True:
            remote.do_remote_call(socket, False, allowed_methods=['geocode_remote'], 
                                  extra_kwargs={'timer':timer})
            
class ImportThread(Thread):
    def run(self):
        in_socket=remote.create_socket(self.context, 'server')
        while True:
            remote.do_remote_call(in_socket)
        
    
            
        
class Command(BaseCommand):
    option_list=BaseCommand.option_list + \
    (make_option("-d", "--debug",  help="Switch on debug messaging" , action="store_true"),)
    
    def handle(self, *args, **options ):
        if options.get('debug'):
            logging.getLogger().setLevel(logging.DEBUG)
            
        remote.init()
        ctx=remote.context(True)
        remote.run_proxy( ctx)
        gc=GeocoderThread(ctx)
        gc.start()
        importer=ImportThread(ctx)
        importer.start()
        while True:
            time.sleep(60)
       
       