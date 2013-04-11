# -*- coding: utf-8 -*-

import base64
from collections import OrderedDict
import gittkt
import gitshelve
import json
import os
import shutil
import sys
import tempfile
import unittest
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
class t_gittkt(unittest.TestCase):
    def setUp(self):
        """Create a new git repository, cd to it, and create the initial 
           commit"""
        self.gitDir = tempfile.mkdtemp()
        self.lastCWD = os.getcwd()
        os.chdir(self.gitDir)
        gitshelve.git('init')
        self.stream = StringIO()
        self.branch = 'git-tkt'
        self.gittkt = gittkt.GitTkt(branch = self.branch,
                             non_interactive = True,
                             save = False,
                             loadShelves = ['active'],
                             outstream = self.stream)

    def tearDown(self):
        """Delete the git repository"""
        os.chdir(self.lastCWD)
        shutil.rmtree(self.gitDir)
        self.stream.close()

    def testRun(self):
        command = 'archives'
        def printHelpFunc():
            pass
        self.gittkt.Run(command,printHelpFunc)
        self.assertRaises(gittkt.GitTktError,
                          self.gittkt.Run,command,printHelpFunc,'fail')

    def testLoadFields(self):
        fields = gittkt.LoadFields()
        #assert the default fields are loaded
        self.assertIn('name',fields)
        self.assertIn('description',fields)
        self.assertIn('author',fields)

        with self.assertRaises(gittkt.GitTktError): 
            gittkt.LoadFields(os.path.join(SCRIPT_DIR,
                                   'TestFieldsFile_err.xml'))

        fields = gittkt.LoadFields(os.path.join(SCRIPT_DIR,
                                   'TestFieldsFile.xml'))
        #assert the expected fields are loaded
        self.assertIn('author',fields)
        self.assertGreater(len(fields['author'].default),0)
        fields['author'].SetValue('Thurston')

    def testArchives(self):
        #test with no archive
        self.gittkt.Archives()
        self.assertRegexpMatches(self.stream.getvalue(),"No archives found.")

        #test with some shelves
        shelf = gitshelve.open(self.branch)
        shelf['active/numbers.txt'] = 'text'
        shelf['archived/numbers.txt'] = 'text'
        shelf.commit()

        self.stream.truncate(0)
        self.gittkt.Archives()
        self.assertRegexpMatches(self.stream.getvalue(),"active\narchived\n")
        
if __name__ == '__main__':
    unittest.main()
