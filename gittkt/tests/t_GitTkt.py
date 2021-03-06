# -*- coding: utf-8 -*-

import base64
from collections import OrderedDict
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

dirName = os.path.dirname(__file__)
parentDir = (os.path.abspath(os.path.join(dirName,"..")))
if parentDir not in sys.path:
    sys.path.insert(0,parentDir)
import GitTkt
import gitshelve

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))

class t_GitTkt(unittest.TestCase):
    def setUp(self):
        """Create a new git repository, cd to it, and create the initial 
           commit"""
        self.gitDir = tempfile.mkdtemp()
        self.lastCWD = os.getcwd()
        os.chdir(self.gitDir)
        gitshelve.git('init')
        self.stream = StringIO()
        self.branch = 'git-tkt'
        self.gittkt = GitTkt.GitTkt(branch = self.branch,
                             nonInteractive = True,
                             save = False,
                             loadFolders = ['active'],
                             outstream = self.stream)

    def tearDown(self):
        """Delete the git repository"""
        os.chdir(self.lastCWD)
        shutil.rmtree(self.gitDir)
        self.stream.close()

    def testRun(self):
        command = 'folders'
        def printHelpFunc():
            pass
        self.gittkt.Run(command,printHelpFunc)
        self.assertRaises(GitTkt.GitTktError,
                          self.gittkt.Run,command,printHelpFunc,'fail')

    def testLoadFields(self):
        fields = GitTkt.LoadFields()
        #assert the default fields are loaded
        self.assertIn('name',fields)
        self.assertIn('description',fields)
        self.assertIn('author',fields)

        with self.assertRaises(GitTkt.GitTktError): 
            GitTkt.LoadFields(os.path.join(SCRIPT_DIR,
                                   'TestFieldsFile_err.xml'))

        fields = GitTkt.LoadFields(os.path.join(SCRIPT_DIR,
                                   'TestFieldsFile.xml'))
        #assert the expected fields are loaded
        self.assertIn('author',fields)
        self.assertGreater(len(fields['author'].default),0)
        fields['author'].SetValue('Thurston')

    def testFolders(self):
        #test with no folders
        self.gittkt.Folders()
        self.assertRegexpMatches(self.stream.getvalue(),"No folders found.")

        #test with some shelves
        shelf = gitshelve.open(self.branch)
        shelf['active/numbers.txt'] = 'text'
        shelf['archived/numbers.txt'] = 'text'
        shelf.commit()

        self.stream.truncate(0)
        self.gittkt.Folders()
        self.assertRegexpMatches(self.stream.getvalue(),"active\narchived\n")
        
if __name__ == '__main__':
    unittest.main()
