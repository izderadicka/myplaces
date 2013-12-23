'''
Created on Jun 19, 2013

@author: ivan
'''
#import gevent.monkey
#gevent.monkey.patch_all()
#import zmq.green as zmq



import sys
import time
import multiprocessing
import threading
import os
import uuid
import base64
import pickle
import logging

log=logging.getLogger('mp.remote')


ADDR='tcp://127.0.0.1:9999'
ADDR_SUB='ipc://test_workers'
ADDR_PUB='tcp://127.0.0.1:9998' 

_REMOTE_METHODS={}
_PROCESS_LIMIT=2

#adapt to take settings from django config if available
try:
    from django.conf import settings
    ADDR=settings.REMOTE_ADDR_IMPORT  or ADDR
    ADDR_SUB=settings.REMOTE_ADDR_IMPORT_PROXY or ADDR_SUB
    ADDR_PUB=settings.REMOTE_ADDR_IMPORT_BROADCAST
except:
    pass

def init(green=False):
    global zmq
    if green:
        import zmq.green as zmq
    else:
        import zmq

def set_processes_limit(lim):
    _PROCESS_LIMIT=lim

def is_remote(fn):
    _REMOTE_METHODS[fn.__name__]=fn
    return fn

def send_msg(socket, stream_id, type, data):
    data=pickle.dumps(data)
    socket.send_multipart((stream_id, type, data))
    
def recv_msg(socket):
    stream_id, type, data=socket.recv_multipart()
    return stream_id, type, pickle.loads(data)

def poll_msg(socket, cb_fn, timeout=3600):
    poller=zmq.Poller()
    poller.register(socket, zmq.POLLIN)
    while True:
        available=dict(poller.poll(timeout*1000))
        if available.get(socket)==zmq.POLLIN:
            stream_id, mtype, data=socket.recv_multipart()
            if cb_fn(stream_id, mtype, pickle.loads(data)):
                return
        else:
            raise TimeoutError()

def sub_msg(socket, stream_id):
    socket.setsockopt(zmq.SUBSCRIBE, stream_id)
    
class RemoteError(Exception):
    pass
class BusyError(RemoteError):
    pass
class TimeoutError(RemoteError):
    pass

ERROR_TAG='__ERROR__'
BUSY_TAG='__BUSY__'
RESULT_TAG='__RES__'
def call_remote(socket, method, args, call_id='', timeout=3):
    if isinstance(call_id, unicode):
        call_id=call_id.encode('utf-8') 
    socket.send_multipart((method, call_id, pickle.dumps(args)))
    poller=zmq.Poller()
    poller.register(socket, zmq.POLLIN)
    ready=dict(poller.poll(timeout*1000))
    if ready and ready.has_key(socket):
        result, resp=socket.recv_multipart()
    else:
        raise TimeoutError('No response from server')
    if result==ERROR_TAG:
        raise RemoteError(str(resp))
    elif result==BUSY_TAG:
        raise BusyError(str(resp))
    elif result==RESULT_TAG:
        resp=pickle.loads(resp)
    return resp

_running={}
class AlreadyRunning(Exception):
    pass
def _check_running(call_id):
    children=multiprocessing.active_children()
    children_pids=set([x.pid for x in children])
    to_del=[]
    for pid in _running:
        if pid not in children_pids:
            to_del.append(pid)
    for pid in to_del:
        del _running[pid]
    if call_id and call_id in set(_running.values()):
        raise AlreadyRunning()
        
    return len(children)


def do_remote_call(socket, new_proc=True, allowed_methods=None, extra_kwargs={}):
    def _err(msg,e=None):
        socket.send_multipart((ERROR_TAG, msg))
        log.error(msg)
        if e:
            log.exception(str(e))
    method, call_id, args= socket.recv_multipart()
    
    if allowed_methods and method not in allowed_methods:
        _err('Forbidden method %s'% method)
        return
    
    if new_proc:
        try:
            running_processes=_check_running(call_id)
        except AlreadyRunning:
            _err('Process for call_id %s is already running'%call_id)
            return
        if running_processes>=_PROCESS_LIMIT:
            socket.send_multipart((BUSY_TAG, 'Reached process limit of %d'%_PROCESS_LIMIT))
            log.info('Reached processes limit of %d'% _PROCESS_LIMIT)
            return
    
    fn=_REMOTE_METHODS.get(method)
    if not fn and not callable(fn):
        _err( 'Uknown method %s'%method)
        return
        
    try:
        args=pickle.loads(args)
        if not isinstance(args, (list, tuple)):
            _err( 'Invalid arguments, must be tuple or list')
            return
    except Exception, e:
        _err( 'Error while deserializing args - %s'% str(e))
        return
    
    if new_proc:
        try:
            p=multiprocessing.Process(target=fn, args=args, kwargs=extra_kwargs)
            p.start()
        except Exception,e:
            _err('Error while starting process %s'%str(e))    
        pid=p.pid
        log.debug("Started process %d for %s(%s)", pid, method, args)
        if call_id and pid:
            _running[pid]=call_id
        socket.send_multipart(('',str(pid)))
        
    else:
        res=None
        try:
            res=fn(*args, **extra_kwargs)
        except Exception, e:
            _err('Function error: %s' % str(e), e)
            return
        socket.send_multipart((RESULT_TAG, pickle.dumps(res)))
        

def run_proxy(context):   
    proxy=zmq.devices.ThreadDevice(zmq.QUEUE, zmq.XSUB,zmq.XPUB )
    proxy.bind_in(ADDR_SUB)
    #proxy.setsockopt_in(zmq.SUBSCRIBE, '')
    proxy.bind_out(ADDR_PUB)
    proxy.start() 

def run_proxy3(ctx):    
    in_sock=ctx.socket(zmq.XSUB)
    in_sock.bind(ADDR_SUB)
    out_sock=ctx.socket(zmq.XPUB)
    out_sock.bind(ADDR_PUB)
    proxy=zmq.device(zmq.QUEUE,in_sock, out_sock)

def run_proxy2(ctx):
    
    def proxy():
        xpub = ctx.socket(zmq.XPUB)
        xpub.bind(ADDR_PUB)
        xsub = ctx.socket(zmq.XSUB)
        xsub.bind(ADDR_SUB)  
        poller = zmq.Poller()
        poller.register(xpub, zmq.POLLIN)
        poller.register(xsub, zmq.POLLIN)
        while True:
            events = dict(poller.poll(1000))
            if xpub in events:
                message = xpub.recv_multipart()
                xsub.send_multipart(message)
            if xsub in events:
                message = xsub.recv_multipart()
                xpub.send_multipart(message)
                
    t=threading.Thread(target=proxy)
    t.setDaemon(True)
    t.start()

def context(force_new=False):
    if force_new:
        return zmq.Context()
    else:
        return zmq.Context.instance()

def create_socket(context,stype, linger=100):
    stype=stype.lower()
    if stype=='client':
        socket=context.socket(zmq.REQ)
        socket.connect(ADDR)
    elif stype=='server':
        socket=context.socket(zmq.REP)
        socket.bind(ADDR)
    elif stype=='pub':
        socket=context.socket(zmq.PUB)
        socket.connect(ADDR_SUB)
    elif stype=='sub':
        socket=context.socket(zmq.SUB)
        socket.connect(ADDR_PUB)
    else:
        raise ValueError('Invalid socket type')
    
    socket.setsockopt(zmq.LINGER,linger)
    return socket
        
@is_remote
def process(token):
    # need new context after forking
    pid=str(os.getpid())
    ctx=context(True)
    pub=create_socket(ctx, 'pub')
    for i in range(10):
        time.sleep(0.1)
        print 'Sending from %s' % pid
        send_msg(pub,  pid, 'msg', {'process':pid, 'step':i, 'token':token})
        
    send_msg(pub, pid,'done', pid)    
    pub.close()
#    ctx.term()   



def server():
    ctx=context()
    in_socket=create_socket(ctx, 'server')
    run_proxy( ctx)
    while True:
        do_remote_call(in_socket)
    in_socket.close()
        
def client():
    ctx=context()
    out_socket=create_socket(ctx, 'client')
    token=base64.b64encode(uuid.uuid4().bytes)
    pid=call_remote(out_socket, 'process', [token])
    print 'Send token: ', token, ' got pid ', pid
        #time.sleep(0.1)
        
    msg_socket=create_socket(ctx, 'sub')
    sub_msg(msg_socket, pid)
    count=0
    while True:
        stream_id, mtype, msg=recv_msg(msg_socket)
        if mtype=='msg':
            print 'Received message', msg
            count+=1
        elif mtype=='done':
            print 'Done', msg
            break
        else:
            print type(mtype), mtype, mtype=='msg'
    msg_socket.close()
    out_socket.close()
    #for some reason term hangs??
    #ctx.term()
    return count
    
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    init()
   
    if len(sys.argv)>1 and sys.argv[1]=='server':
        server()
    else:
        client()
    
    
        