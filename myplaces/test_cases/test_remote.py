'''
Created on Aug 29, 2013

@author: ivan
'''
import unittest
import subprocess
import time
import threading
import base64,uuid

from myplaces import remote



def client( token=None):
    
    out_socket=remote.create_socket(ctx, 'client')
    token=token or base64.b64encode(uuid.uuid4().bytes)
    try:
        pid=remote.call_remote(out_socket, 'process', [token], call_id=token)
        print 'Send token: ', token, ' got pid ', pid
    except remote.RemoteError, e:
        threading.current_thread().result=e
        return
    finally:
        out_socket.close()  
      
    msg_socket=remote.create_socket(ctx, 'sub')
    remote.sub_msg(msg_socket, pid)
    count=0
    while True:
        stream_id, mtype, msg=remote.recv_msg(msg_socket)
        if mtype=='msg':
            print 'Received message', msg
            if msg['token']==token:
                count+=1
        elif mtype=='done':
            print 'Done', msg
            break
        else:
            raise Exception('Invalid msg type')
    msg_socket.close()
    
    threading.current_thread().result=count
    
    #for some reason term hangs??
    #ctx.term()
    return count

ctx=None
class TestRemote(unittest.TestCase):


    def setUp(self):
        self.server=subprocess.Popen(['python', remote.__file__, 'server'], shell=False)
        
        global ctx
        if not ctx:
            remote.init()
            ctx=remote.context()

    def tearDown(self):
        self.server.kill()


    def test_remote(self):
        time.sleep(1)
       
        
        threads=[]
        for i in range(remote._PROCESS_LIMIT):
            t=threading.Thread(target=client)
            t.daemon=True
            t.start()
            threads.append(t)
        time.sleep(0.2)
        over_limit=threading.Thread(target=client)
        over_limit.start()
        for i in range(len(threads)):
            threads[i].join(10)
        over_limit.join(10)
        for i in range(len(threads)):
            self.assertEqual(threads[i].result, 10)
        self.assertTrue(isinstance(over_limit.result, remote.BusyError))
        
    def test_repeated_call(self):
        time.sleep(1)
        t1=threading.Thread(target=client, args=('token1',))
        t2=threading.Thread(target=client,args=('token1',))
        t1.start()
        time.sleep(0.1)
        t2.start()
        t1.join(10)
        t2.join(10)
        self.assertEqual(t1.result, 10)
        self.assertTrue(isinstance(t2.result, remote.RemoteError))
        
        


if __name__ == "__main__":
    import sys;sys.argv = ['', 'TestRemote.test_repeated_call']
    unittest.main()