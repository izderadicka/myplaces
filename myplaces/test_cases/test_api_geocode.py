# encoding=utf-8
'''
Created on Nov 4, 2013

@author: ivan
'''
import unittest
import myplaces.remote as remote
import os
import subprocess
import rest_framework.test as test


class TestApiGeocode(test.APITestCase):
    fixtures=["test_data_auth.json"]

    def setUp(self):
        remote.init()
        manage=os.path.join(os.path.split(__file__)[0], '../../manage.py')
        self.p=subprocess.Popen(['python', manage,  'process_server'], shell=False)
    
        
    def tearDown(self):
        self.p.kill()

    def test_reverse(self):
        self.client.login(username="user", password="user")
        resp=self.client.post('/mp/api/geocode/reverse', {'position': [49.9506159,14.3155932]}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['address']['city'], u'Černošice')
        self.client.login(username='dummy', password="dummy")
        resp=self.client.post('/mp/api/geocode/reverse', {'position': [49.9506159,14.3155932]}, format='json')
        self.assertEqual(resp.status_code, 403)
            


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()