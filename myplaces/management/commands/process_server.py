'''
Created on Jun 19, 2013

@author: ivan
'''

from django.core.management.base import BaseCommand, CommandError
import myplaces.remote as remote
import myplaces.implaces as implaces
import os
from django.utils.translation import ugettext as _
import logging
from optparse import make_option


@remote.is_remote
def import_places(stream_id, temp_file, mapping, name, description, 
                  private,  user,  existing='update', encoding='utf-8'):
    ctx=remote.context()
    pub_socket=remote.create_socket(ctx, 'pub')
    def report_error(line,msg):
        remote.send_msg(pub_socket, stream_id, 'error', {'line':line, 'msg':msg})
    def report_progress(line, total):
        remote.send_msg(pub_socket, stream_id, 'progress', {'line':line, total:'total'})
        
    try:    
        implaces.import_places(temp_file, mapping, name, description, private, user, existing, encoding,  
                               report_error, report_progress)
        remote.send_msg(pub_socket, stream_id, 'done', '')
    finally:
        pub_socket.close()

class Command(BaseCommand):
    option_list=BaseCommand.option_list + \
    (make_option("-d", "--debug",  help="Switch on debug messaging" , action="store_true"),)
    
    def handle(self, *args, **options ):
        if options.get('debug'):
            logging.getLogger().setLevel(logging.DEBUG)
            
        remote.init()
        remote.server()