'''
Created on Dec 20, 2013

@author: ivan
'''
import unittest
from lxml import etree
from StringIO import StringIO


class Test(unittest.TestCase):


    def testLXML(self):
        nsmap={None: 'default_namespace_uri'}
        root=etree.Element('{default_namespace_uri}elem', {'{default_namespace_uri}attrib':'xyz'}, nsmap=nsmap )
        stream=StringIO()
        tree=etree.ElementTree(root)
        tree.write(stream)
        print etree.__version__
        print stream.getvalue()

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()