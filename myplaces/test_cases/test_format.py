'''
Created on Dec 14, 2013

@author: ivan
'''
import unittest


class TestFormat(unittest.TestCase):


    def testIndex(self):
        import myplaces.format as fmt
        index=fmt.index()
        self.assertEqual(len(index),3)
        self.assertEqual(index[0][0], 'CSV')
        self.assertEqual(index[2][0], 'GEOJSON')


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testIndex']
    unittest.main()