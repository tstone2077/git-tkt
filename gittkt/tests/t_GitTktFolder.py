# -*- coding: utf-8 -*-
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
import GitTktFolder
import GitTkt
import gitshelve

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))

class t_GitTktFolder(unittest.TestCase):
    def setUp(self):
        """Create a new git repository, cd to it, and create the initial 
           commit"""
        self.gitDir = tempfile.mkdtemp()
        self.lastCWD = os.getcwd()
        os.chdir(self.gitDir)
        gitshelve.git('init')
        self.stream = StringIO()
        self.branch = 'git-tkt'
        self.gitTktFolder = GitTktFolder.GitTktFolder(name = 'active',
            branch = self.branch,
            fields = GitTkt.LoadFields(),
            outstream = self.stream)

    def tearDown(self):
        """Delete the git repository"""
        os.chdir(self.lastCWD)
        shutil.rmtree(self.gitDir)
        self.stream.close()

    def testAdd(self):
        ticketDataOld = {
            'field1' : 'data1',
            'field2' : 'data2',
            }
        ticketId = self.gitTktFolder.Add(ticketDataOld.copy())
        #assert that the ticket was added to the shelf
        shelf = gitshelve.open(branch = self.branch)
        data = eval(shelf['active/%s'%ticketId])
        newData = {}
        for key,value in data.items():
            if key not in GitTktFolder.GITTKT_RESERVED_FIELD_NAMES:
                newData[key] = value
                
        self.assertEqual(ticketDataOld,newData)
        #verify the number map is setup correctly
        data = shelf['active/%s'%GitTktFolder.GITTKT_NUM_MAP_FILE]
        ticketNumFile = "1\t%s\n"%ticketId
        self.assertEqual(str(data),ticketNumFile)

        #verify we strip out uuid and num from the ticket data
        ticketDataNew = {
            'field1' : 'data1',
            'field2' : 'data2',
            'uuid'   : 'data3',
            'num'    : '1',
            }
        ticketId = self.gitTktFolder.Add(ticketDataNew)
        #assert that the ticket was added to the shelf
        shelf = gitshelve.open(branch = self.branch)
        data = eval(shelf['active/%s'%ticketId])
        newData = {}
        for key,value in data.items():
            if key not in GitTktFolder.GITTKT_RESERVED_FIELD_NAMES:
                newData[key] = value
        self.assertEqual(ticketDataOld,newData)

        data = shelf['active/%s'%GitTktFolder.GITTKT_NUM_MAP_FILE]
        ticketNumFile += "2\t%s\n"%ticketId
        self.assertEqual(str(data),ticketNumFile)

if __name__ == '__main__':
    unittest.main()
