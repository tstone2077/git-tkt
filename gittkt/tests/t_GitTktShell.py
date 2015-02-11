# -*- coding: utf-8 -*-

import os
import sys
#import t_gitshelve
import unittest

dirName = os.path.dirname(__file__)
parentDir = (os.path.abspath(os.path.join(dirName,"..")))
if parentDir not in sys.path:
    sys.path.insert(0,parentDir)

import GitTkt
import GitTktShell

class t_GitTktShell(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

class InputInjection(object):
    def __init__(self):
        self.raw_input = GitTktShell.raw_input
        GitTktShell.raw_input = lambda *_: self.data
        self.data = ""

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        GitTktShell.raw_input = self.raw_input
if __name__ == '__main__':
    unittest.main()
