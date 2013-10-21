
import os
import re
import importlib
import unittest
from django import test

TESTS_DIR='test_cases'

curr_dir=os.path.split(__file__)[0]
tests_dir=os.path.join(curr_dir, TESTS_DIR)


def is_test_case(cls):
    return issubclass(cls, unittest.TestCase ) and cls!= unittest.TestCase and cls!=test.TestCase

files=os.listdir(tests_dir)
for f in files:
    m=re.match('^test.*\.py$', f, re.IGNORECASE)
    mod_name=os.path.splitext(f)[0]
    
    if m:
        mod=importlib.import_module(os.path.basename(curr_dir)+'.'+TESTS_DIR+'.'+mod_name)
        for name in dir(mod):
            mbr=getattr(mod, name)
            if isinstance(mbr, type) and is_test_case(mbr):
                globals()[name]=mbr
                print 'Found test case', name
                
                


