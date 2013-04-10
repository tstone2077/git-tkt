# -*- coding: utf-8 -*-

import gittkt
import gitshelve
import os
import shutil
import sys
import tempfile
import unittest
from StringIO import StringIO

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

    def testShelves(self):
        #test with no shelf
        self.gittkt.shelves(None,None)
        self.assertRegexpMatches(self.stream.getvalue(),"No shelves found.")

        #test with some shelves
        shelf = gitshelve.open(self.branch)
        shelf['active/numbers.txt'] = 'text'
        shelf['archived/numbers.txt'] = 'text'
        shelf.commit()

        self.stream.truncate(0)
        self.gittkt.shelves()
        self.assertRegexpMatches(self.stream.getvalue(),"active\narchived\n")
        
if __name__ == '__main__':
    unittest.main()
