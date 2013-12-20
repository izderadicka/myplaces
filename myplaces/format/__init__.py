import os
import re
from django.utils.translation import ugettext_lazy
import logging
import sys
import threading
log=logging.getLogger('mp.format')

class Format(object):
    def __init__(self, 
                 name, desc, module, sort_order=sys.maxint, mime='application/octet-stream', extensions=None):
        self.name=name
        self.desc=desc
        self.module=module
        self.sort_order=sort_order
        self.mime=mime
        self.extensions=extensions
        self._reader=None
        self._import_addon=None
        self._is_imported=False
        self._export_adapter=None
        self._lock=threading.RLock()
        
    def register_reader(self, reader):
        with self._lock:
            self._reader=reader
            
    def register_import_addon(self, addon):
        with self._lock:
            self._import_addon=addon
            
    def register_export_adapter(self, adapter):
        with self._lock:
            self._export_adapter=adapter
        
    @property    
    def reader(self):
        with self._lock:
            self._check_resolved()
            return self._reader
        
    @property    
    def import_addon(self):
        with self._lock:
            self._check_resolved()
            return self._import_addon
        
    @property
    def export_adapter(self):
        with self._lock:
            self._check_resolved()
            return self._export_adapter
        
    
    def _check_resolved(self):
        if not self._is_imported:
            __import__('myplaces.format', fromlist=[self.module])
            self._is_imported=True
    
    
       
        
class Registery(dict): 
    #assuming small number of formats - up to 20 lookup is comparable with hash table
    def get_by_module(self,mod):
        for fmt in self.values():
            if mod==fmt.module:
                return fmt    
_register=Registery()

def get_fmt_descriptor(name):
    fmt=_register.get(name)
    if not fmt:
        raise KeyError('Invalid format name')
    return fmt

def _get_fmt_from_class(cls):
    mod=cls.__module__.split('.')[-1]
    fmt= _register.get_by_module(mod)
    if not fmt:
        raise TypeError('Not used on format module')
    return fmt


# class decorator to indicate appropriate componnets of format module definition
def import_reader(cls):
    fmt= _get_fmt_from_class(cls)
    fmt.register_reader(cls)
    return cls

def import_addon(cls):
    fmt= _get_fmt_from_class(cls)
    fmt.register_import_addon(cls)
    return cls

def export_adapter(cls):
    fmt= _get_fmt_from_class(cls)
    fmt.register_export_adapter(cls)
    return cls

def index():
    idx=[(_register[key].sort_order, key, _register[key].desc) for key in _register]
    idx.sort(key=lambda i: i[0])
    return [(key, desc) for (_sort, key, desc) in idx]

def _scan_formats():
    def get_val(name):
        base_regex=r'^%s\s*=\s*[\'"](.*)[\'"]'
        m=re.search(base_regex % name,content, re.MULTILINE )
        return m.group(1)
    
    def get_int(name):
        base_regex=r'^%s\s*=\s*(\d+)'
        m=re.search(base_regex % name,content, re.MULTILINE )
        return int(m.group(1))
    
    def get_list(name):
        v=get_val(name)
        return  map(lambda s: s.strip(), v.split(','))
    
    path =os.path.split(__file__)[0]
    for fname in os.listdir(path):
        fpath=os.path.join(path, fname)
        if os.path.isfile(fpath) and fname.endswith('.py') and not fname.startswith('_'):
            with file(fpath,'rb') as f:
                content= f.read()
            try:
                name=get_val('NAME')
                description=ugettext_lazy(get_val('DESCRIPTION'))
                mime=get_val('MIME')
            except (AttributeError, KeyError):
                log.error('Invalid format module %s'%fname)
                continue
                
            sort=sys.maxint
            extensions=None
            
            try:
                sort=get_int('SORT')
                extensions=get_list('EXTENSIONS')
               
            except (AttributeError, KeyError), e:
                pass
                
            module=os.path.splitext(fname)[0]  
            
            _register[name]=Format(name, description, module, sort, mime, extensions)
            
_scan_formats()


class FileReader(object):
    ''' Read individual places from a file,  abstracts file format'''
    
    def __init__(self, file_name, extra_params):
        pass
    
    def next(self):
        '''Return next record or raise StopIteration
returns dictionary with following keys:
name   (mandatory)
description  
url
position (tuple longitute, latitude - e.g decimal valuses, switched order then in normal geographic notation)
address  (dictionary)
    street
    city
    postal_code
    county
    state
    country
    phone
    email
    unformatted (can be flat unformatted address)
    
either position or address must be present - if position is missing import will try to geocode adrress
    
     
'''
        raise NotImplemented
    def count(self):
        '''Return total number of records in the file, None if not known'''
        return None 
    
    def close(self):
        '''Closes any resources'''
        pass
    
    def __iter__(self):
        return self
    
    #implemets context manager interface
    def __enter__(self):
        return self
    
    def __exit__(self,exc_type, exc_value, traceback):
        self.close()
                    
                
class ImportFormAddon(object):
    template='upload2.html' # must extend this template
    def extend_context(self, file_name, ctx ,encoding='utf-8'):    
        """ Should add to context any variables that are needed for rendering of customize upload template"""
        pass
     
    def process_form(self, data):    
        """Processes data posted from upload form
returns  tuple  extra_params, errors
extra_params -   format specific data - to be passed to instance of FileReader
errors - list of error messages or None is data are OK     
        """
        return None, None
    
class ExportAdapter(object):
    def __init__(self, response):
        self.response=response
        
    def export(self, group, places):
        raise NotImplemented
            