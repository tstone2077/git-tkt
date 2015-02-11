# -*- coding: utf-8 -*-

import os
import sys
import unittest
from t_GitTktShell import InputInjection
from helpers import NoStdStreams

dirName = os.path.dirname(__file__)
parentDir = (os.path.abspath(os.path.join(dirName,"..")))
if parentDir not in sys.path:
    sys.path.insert(0,parentDir)
import gittktCLI

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))

class t_gittktCLI(unittest.TestCase):
    def setUp(self):
        # use environment variables to set author and committer.
        # using the config didn't work in travis-ci.org.
        os.environ["GIT_AUTHOR_NAME"] = "John Doe"
        os.environ["GIT_AUTHOR_EMAIL"] = "doe.j@example"
        os.environ["GIT_COMMITTER_NAME"] = "John Doe"
        os.environ["GIT_COMMITTER_EMAIL"] = "doe.j@example"

    def tearDown(self):
        del os.environ["GIT_AUTHOR_NAME"]
        del os.environ["GIT_AUTHOR_EMAIL"]
        del os.environ["GIT_COMMITTER_NAME"]
        del os.environ["GIT_COMMITTER_EMAIL"]

    def testParseArgs(self):
        args = ['name', '--verbose','debug', '--load-fields-file',
                os.path.join(SCRIPT_DIR,'TestFieldsFile.xml')]
        results,fields = gittktCLI.ParseArgs(args)
        self.assertRegexpMatches('debug',results.verbose)
        self.assertIn('author',fields.keys())
        self.assertNotIn('description',fields.keys())

    def testMain(self):
        with NoStdStreams():
            args = ['unittest','help']
            self.assertEqual(gittktCLI.Main(args),0)

        inject = InputInjection()
        with NoStdStreams():
            with inject:
                inject.data = 'exit'
                args = ['unittest']
                self.assertEqual(gittktCLI.Main(args),0)

    def testEntryPoint(self):
        with NoStdStreams():
            with NewSysArgv(['name','--show-traceback','help','-x']):
                self.assertRaises(gittktCLI.ArgParseError,
                                  gittktCLI.EntryPoint,False)
            with NewSysArgv(['name','help','-x']):
                gittktCLI.EntryPoint(False)
        
class NewSysArgv(object):
    def __init__(self,args):
        self.args = args
        self.originalArgs = sys.argv
    def __enter__(self):
        sys.argv = self.args
    def __exit__(self, exc_type, exc_value, traceback):
        sys.argv = self.originalArgs

if __name__ == '__main__':
    unittest.main()
