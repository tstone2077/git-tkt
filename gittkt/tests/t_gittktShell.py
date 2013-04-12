# -*- coding: utf-8 -*-

import os
import sys
import unittest

dirName = os.path.dirname(__file__)
parentDir = (os.path.abspath(os.path.join(dirName,"..")))
if parentDir not in sys.path:
    sys.path.insert(0,parentDir)

import gittkt
import gittktShell

class t_gittktShell(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

class NoStdStreams(object):
    def __init__(self):
        self.devnull = open(os.devnull,'w')
        self._stdout = self.devnull or sys.stdout
        self._stderr = self.devnull or sys.stderr

    def __enter__(self):
        self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
        self.old_stdout.flush(); self.old_stderr.flush()
        sys.stdout, sys.stderr = self._stdout, self._stderr

    def __exit__(self, exc_type, exc_value, traceback):
        self._stdout.flush(); self._stderr.flush()
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
        self.devnull.close()

class InputInjection(object):
    def __init__(self):
        self.raw_input = gittktShell.raw_input
        gittktShell.raw_input = lambda *_: self.data
        self.data = ""

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        gittktShell.raw_input = self.raw_input
if __name__ == '__main__':
    unittest.main()
