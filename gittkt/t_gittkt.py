# -*- coding: utf-8 -*-

import gittkt
import os
import sys
import unittest

class t_gittkt(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testGitTkt(self):
        pass

    def testParseArgs(self):
        args = ['name','--verbose','debug']
        results = gittkt.ParseArgs(args)
        self.assertRegexpMatches('debug',results.verbose)

    def testMain(self):
        with NoStdStreams():
            self.assertEqual(gittkt.Main(['unittest','--verbose','debug']),0)

    def testEntryPoint(self):
        #not sure how to test this, since it runs sys.exit
        pass
        #gittkt.EntryPoint()
        
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


if __name__ == '__main__':
    unittest.main()
