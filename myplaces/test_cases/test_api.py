# -*- coding: utf-8 -*- 
'''
Created on Aug 26, 2013

@author: ivan
'''
import unittest
import types
import base64
import httplib, urllib, urlparse
import json
from copy import copy
from django import test


class ApiError(Exception):
    def __init__(self, status,  msg, body=None):
        self.status=int(status)
        try:
            self.body=json.loads(body) if body else None
        except ValueError:
            self.body=str(body)
        super(ApiError, self).__init__(msg+' ('+str(status)+')')
class ApiClient():
    PLACE='place'
    GROUP="group"
    ADDRESS="address"
    base_path='/mp/api/'
    host="localhost"
    port=8081
    default_headers={'Accept': 'application/json'}
    methods=['GET', 'HEAD', 'OPTIONS', 'POST', 'PUT', 'DELETE', 'PATCH']
    def __init__(self,username=None, password=None):
        
            
        self.headers=copy(self.default_headers)
        
        if username:
            self.headers['Authorization']="Basic "+base64.b64encode(username+":"+password)
        
        
    def _call(self, method, entities, data=None, pk=None, filter=None):
        
        
        if method not in self.methods:
            raise ValueError('Invalid Method')
        
        
        
        def get_conn_path():
            if isinstance(entities,types.StringTypes) and entities.startswith('http'):
                s, host, path, p,query,f= urlparse.urlparse(entities)
                conn=httplib.HTTPConnection(host, None,  strict=True, timeout=10)
                if query:
                    path+="?"+query
                return conn, path
            
            if entities not in (ApiClient.PLACE, ApiClient.GROUP, ApiClient.ADDRESS):
                raise ValueError('Invalid entities name')
            conn=httplib.HTTPConnection(self.host, self.port, strict=True, timeout=10)
            path= self.base_path+entities
            if pk:
                path+='/'+str(pk)
                
            return conn, path
            
        conn, path= get_conn_path()   
        if filter:
            sep="?" if path.find('?')<0 else '&'
            path+=sep+urllib.urlencode(filter)
        headers=copy(self.headers)
        if data:
            data=json.dumps(data)
            headers['Content-Type']="application/json"
        conn.request(method, path, data, headers)
        resp=conn.getresponse()
        if resp.status>=300:
            raise ApiError(resp.status, resp.reason, resp.read())
        
        result=resp.read()
        conn.close()
        if result:
            return json.loads(result)
        
    def get(self, entity, pk=None, filter=None):
        return self._call('GET', entity, None, pk, filter=filter)
    
    def post(self, entity, data):
        return self._call('POST', entity, data)
    
    
    def put(self, entity, data, pk=None):
        return self._call('PUT', entity, data, pk=pk)    
    
    def patch(self, entity, data, pk=None):
        return self._call('PATCH', entity, data, pk=pk)
    
    def delete(self, entity, pk=None):
        return self._call('DELETE', entity, pk=pk)
        
    
    
        
        


class TestApi(test.LiveServerTestCase):

    fixtures=["test_data.json", "test_data_auth.json"]
    def test_access(self):
        c=ApiClient()
        groups=c.get(ApiClient.GROUP)
        self.assertEqual(groups['count'], 3)
            
        c=ApiClient('dummy', 'dummy')
        groups=c.get(ApiClient.GROUP)    
        try:
            res=c.post(ApiClient.GROUP, {'name':'test', 'description':'testovaci unit', 'private':False})
            self.fail('Should not have rights to create')
        except ApiError,e:
            self.assertEqual(e.status, 403)
            
            
    
            
    def test_browse(self):
        c=ApiClient('dummy', 'dummy')
        groups=c.get(ApiClient.GROUP)
        self.assertTrue(groups is not None)
        self.assertTrue(groups['count'], 3)
        
        g1=groups['results'][0]['id']
        
        g1=c.get(ApiClient.GROUP, g1)
        self.assertTrue(len(g1['name'])>3)
        
        
    def test_filter(self):
        c=ApiClient("user", "user")
        
        places=c.get(ApiClient.PLACE, filter={'name':'1'})
        self.assertEqual(places['count'], 1)
        
        pages=0
        entity=ApiClient.PLACE
        filter={"group":3}
        while True:
            places=c.get(entity, filter=filter)
            pages+=1
            entity= places.get('next')
            filter=None
            if not entity:
                break
            
        self.assertEqual(pages,7)
        
        places=c.get(ApiClient.PLACE, filter={'group':1, 'within':'15km', 'from':'49.9505011,14.3151411'})
        self.assertEqual(places['count'], 5)
        
        places=c.get(ApiClient.PLACE, filter={'group':1, 'within':'50km', 'from':'49.9505011,14.3151411',
                                              'q':'pivo une'})
        self.assertEqual(places['count'], 1)
        
        try:
            places=c.get(ApiClient.PLACE, filter={'group':1, 'within':'km', 'from':'49.9505011,14.3151411'}) 
            self.fail('Is invalid filter')
        except ApiError, e:
            self.assertEqual(e.status, 400)
            
        groups=c.get(ApiClient.GROUP, filter={'q':'pivo une'})
        self.assertEqual(groups['count'], 1)
            
            
    def test_sort(self):
        c=ApiClient("user", "user")
        groups=c.get(ApiClient.GROUP, filter={'ordering':'name'})
        first=groups['results'][0]
        groups=c.get(ApiClient.GROUP, filter={'ordering':'-name'})
        last=groups['results'][-1]
        self.assertEqual(first, last)    
                
            
        
        
    def test_create(self):
        c=ApiClient('user', 'user')
        c2=ApiClient('admin', 'admin')
        res=c.post(ApiClient.GROUP, {'name':'test', 'description':'testovaci unit', 'private':False})
        
        try:
            c2.post(ApiClient.GROUP, {'name':'test', 'description':'testovaci unit', 'private':False})
            self.fail('Should not be able to create with same name')
        except ApiError, e:
            self.assertEqual(e.status, 400)
        
        group_id=res['id']\
        
        c.patch(ApiClient.GROUP, {'description':'testovaci test'}, pk=group_id)
        
        res=c.post(ApiClient.ADDRESS, {'street':'Čapajevovo nám. 13', "city":"Růžová", "country":"Česká republika",
                                       'postal_code':'809 22'})
        
        adr_id=res['id']
        
        try:
            res=c.post(ApiClient.PLACE, {"name":"Zajímave místo", "url":"http://nekde.jinde.cz", "address":adr_id,
                                     "group":group_id})
            self.fail('Should fail - position is missing')
        except ApiError,e:
            print str(e), e.body
            self.assertEqual(e.status, 400)
            self.assertTrue(e.body.get('position') is not None)
           
        res=c.post(ApiClient.PLACE, {"name":"Zajímave místo", "url":"http://nekde.jinde.cz", "address":adr_id,
                                     "group":group_id, 'position':[14.5, 50]})
        print res
        try:
            c.post(ApiClient.PLACE, {"name":"Zajímave místo", "url":"http://nekde.jinde.cz", "address":adr_id,
                                     "group":group_id, 'position':'POINT (14.5 50)'})
            self.fail()
        except ApiError, e:
            pass
        
        try:
            c.post(ApiClient.PLACE, {"name":"Zajímave místo", "url":"http://nekde.onde.cz", "address":adr_id,
                                     "group":group_id, 'position':[14.5, 51]})
            self.fail('Should not allow to insert same name')
        except ApiError, e:
            self.assertEqual(e.status, 400)
        
        #update with same values:
        res=c.put(ApiClient.PLACE, res, pk=res['id'])
        
        res=c.put(ApiClient.PLACE,  {"name":"Nejzajímavější místo", "url":"http://nekde.jinde.cz", 
                               "address":adr_id, "group":group_id, 'position':[14.5, 50.2]},
                               pk=res['id'])    
        
        self.assertEqual(res['name'], u"Nejzajímavější místo")
        
        
        # can put partial data?
        try:
            res=c.put(ApiClient.PLACE,  {"name":"Nejnezajímavější místo"},  pk=res['id'])
            self.fail('No partial put')
        except ApiError,e:
            print e.body
        
        
        # use patch for this    
        res=c.patch(ApiClient.PLACE,  {"name":"Nejnezajímavější místo"},  pk=res['id'])
        self.assertEqual(res['name'], u"Nejnezajímavější místo")
        
        res=c.patch(ApiClient.PLACE,  {"url":"http://aaa.com"},  pk=res['id'])
        self.assertEqual(res['url'], u"http://aaa.com")
        
        place_id=res['id']
        # can modify only my entities
        try:
            c2.patch(ApiClient.PLACE,  {"name":"Nejnejzajímavější místo"}, pk=place_id)
            self.fail('Should be protected')
        except ApiError,e:
            self.assertEqual(e.status, 403)
            
        try:
            c2.delete(ApiClient.PLACE, place_id)
            self.fail('Should be protected')
        except ApiError,e:
            self.assertEqual(e.status, 403)    
            
        #delete
        c.delete(ApiClient.PLACE, place_id)
        
        try:
            c.get(ApiClient.PLACE,place_id)
            self.fail('Should be delete')
        except ApiError,e:
            self.assertEqual(e.status, 404)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()