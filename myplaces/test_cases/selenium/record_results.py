'''
Created on Nov 27, 2013

@author: ivan
'''
import myplaces.remote as remote
import zmq
import argparse

RUNNING=0

def process_msg(stream_id, mtype, data):
    global RUNNING
    if mtype=='term':
        return
    elif mtype=='measurement':
        print '%d:%s - %d %s %f' % ((RUNNING, stream_id,)+data)
        if log:
            log.write('%d,%s,%d,%s,%f\n' % ((RUNNING, stream_id,)+data))
            log.flush()
    elif mtype=='start':
        RUNNING+=1
    elif mtype=='stop':
        RUNNING-=1
        
        

ADDR='tcp://127.0.0.1:10101'
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--file', help='results file')
    args=p.parse_args()
    remote.init()
    ctx=remote.context()
    socket=ctx.socket(zmq.SUB)
    socket.bind(ADDR)
    remote.sub_msg(socket, '') #subscribe everything
    log=None
    if args.file:
        log=file(args.file, 'wb')
    try:
        remote.poll_msg(socket, process_msg, 3600)
    finally:
        if log:
            log.close()
    
        
    
    
    
    