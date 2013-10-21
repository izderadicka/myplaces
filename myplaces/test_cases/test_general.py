import unittest
from django.core.urlresolvers import  reverse

from myplaces import utils

class TestGeneralDjango(unittest.TestCase):
    
    def test_reverse(self):
        url=reverse('upload-places', args=[1])
        self.assertTrue(len(url)>5)
        
    def test_serialization(self):
        token=utils.gen_uid()
        msg=utils.deserialize(utils.serialize({'token':token}))
        self.assertEquals(token, msg['token'])