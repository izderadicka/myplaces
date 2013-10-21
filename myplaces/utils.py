'''
Created on Jun 10, 2013

@author: ivan
'''

import pickle
import base64
import uuid
import StringIO


def serialize(o):
    s=pickle.dumps(o)
    return base64.b64encode(s)

def deserialize(s):
    s=base64.b64decode(s)
    return pickle.loads(s)


def gen_uid():
    return base64.b64encode(uuid.uuid4().bytes)

def uni(string):
    if isinstance(string, unicode):
        return string
    elif isinstance(string, str):
        return unicode(string, encoding='utf-8')
    raise ValueError('Only string types allowed')

