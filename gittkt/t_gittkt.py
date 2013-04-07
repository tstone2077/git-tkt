import gitshelve
import gittkt
import os
import re
import shutil
import sys
import tempfile
import unittest

lsTreeRE = re.compile('((\d{6}) (Tree|blob)) ([0-9a-f]{40})\t(start|(.+))$')


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

class t_gittkt(unittest.TestCase):
    gitDir = None
    lastCWD = None
    def GetFieldArgs(self,updates = None):
        if updates is None:
            updates = {}
        fields = gittkt.LoadFields()
        fieldArgs = []
        for field in fields:
            if not field.editable:
                continue
            fieldArgs.append('--%s'%field.name)
            if field.name in updates.keys():
                fieldArgs.append(updates[field.name])
            else:
                fieldArgs.append('data')
        return fieldArgs

    def GetAddedTicketIds(self,outputStr):
        matchObj = re.match("Added Ticket #(?P<num>[0-9]+) \((?P<uuid>.+)\)",
                            outputStr)
        num,uuid = None,None
        if matchObj is not None:
            num = matchObj.group('num')
            uuid = matchObj.group('uuid')
        return num,uuid

    def testSaveParameter(self):
        args = ['gittkt.py','--branch','test','--save','new']
        args.extend(self.GetFieldArgs())
        retval = gittkt.Main(args)
        self.assertRegexpMatches(retval, "Storing config data: --branch 'test'")
        args = ['gittkt.py','new']
        args.extend(self.GetFieldArgs())
        retval = gittkt.Main(args)
        self.assertRegexpMatches(retval,"Using config data: --branch 'test'")
        self.assertRegexpMatches(retval,"Added Ticket #2")

        #Test saving when git was created with --separate-git-dir
        try:
            workingCopyDir = tempfile.mkdtemp()
            separatedGitDir = tempfile.mkdtemp()
            lastCWD = os.getcwd()
            os.chdir(workingCopyDir)
            gitshelve.git('init','--separate-git-dir',separatedGitDir)

            args = ['gittkt.py','--branch','test','--save','new']
            args.extend(self.GetFieldArgs())
            retval = gittkt.Main(args)
            self.assertRegexpMatches(retval,
                "Storing config data: --branch 'test'")
        finally:
            #cleanup
            os.chdir(lastCWD)
            shutil.rmtree(separatedGitDir)
            shutil.rmtree(workingCopyDir)
        
    def testNonInteractiveParameter(self):
        args = ['gittkt.py','--non-interactive','new']
        self.assertRaises(gittkt.GitTktError,gittkt.Main,args)

        args = ['gittkt.py','--non-interactive','new']
        args.extend(self.GetFieldArgs())
        retval = gittkt.Main(args)

    def testBranchParameter(self):
        #we need to make a new ticket, so run the new test on differnt
        #branches
        self.testNew('test')
        self.testNew('test2')

    def testHelp(self):
        #test help subcommand (need to hijack stderr
        with NoStdStreams():
            args = ['gittkt.py','help']
            retval = gittkt.Main(args)

    def testNew(self,branch = None):
        #test help subcommand (need to hijack stderr
        with NoStdStreams():
            args = ['gittkt.py','new','help']
            retval = gittkt.Main(args)

        args = ['gittkt.py']
        if branch is None:
            branch = gittkt.GIT_TKT_DEFAULT_BRANCH
        else:
            args.extend(['--branch',branch])
        args.append('new')
        args.extend(self.GetFieldArgs())
        retval = gittkt.Main(args)
        num,uuid = self.GetAddedTicketIds(retval)
        self.assertIsNotNone(num,
                             "output '%s' not formatted as expected"%(retval))

        #verify the added ticket is in the branch we expect it to be in
        data = gitshelve.git('cat-file','-p','%s:active/%s'%(branch,uuid))
        self.assertTrue(len(data) > 0)
        lsTree = gitshelve.git('ls-tree','--full-tree','-r',branch)
        files = []
        for line in lsTree.split("\n"):
            matchObj = lsTreeRE.match(line)
            self.assertIsNotNone(matchObj,
                            "regex not correct for git ls-tree output format.")
            files.append(matchObj.group(5))
        self.assertIn(gittkt.GIT_TKT_NUM_MAP_FILE, files)
        self.assertIn('active/%s'%uuid, files)

    def testShow(self):
        #test help subcommand (need to hijack stderr
        with NoStdStreams():
            args = ['gittkt.py','show','help']
            retval = gittkt.Main(args)
        args = ['gittkt.py','new']
        args.extend(self.GetFieldArgs())
        retval = gittkt.Main(args)
        localId,uuid = self.GetAddedTicketIds(retval)

        args = ['gittkt.py','show',localId]
        retval = gittkt.Main(args)
        self.assertRegexpMatches(retval,'NAME = \w+')

        args = ['gittkt.py','show',uuid]
        retval = gittkt.Main(args)
        self.assertRegexpMatches(retval,'NAME =')

        args = ['gittkt.py','show','100']
        self.assertRaises(gittkt.GitTktError,gittkt.Main,args)

    def testList(self):
        #test help subcommand (need to hijack stderr
        with NoStdStreams():
            args = ['gittkt.py','list','help']
            retval = gittkt.Main(args)
        args = ['gittkt.py','new']
        args.extend(self.GetFieldArgs())
        retval = gittkt.Main(args)

        args = ['gittkt.py','new']
        args.extend(self.GetFieldArgs())
        retval = gittkt.Main(args)

        args = ['gittkt.py','new']
        args.extend(self.GetFieldArgs())
        retval = gittkt.Main(args)

        args = ['gittkt.py','list']
        retval = gittkt.Main(args)
        self.assertRegexpMatches(retval,'1  | data')
        self.assertRegexpMatches(retval,'3  | data')

    def testPull(self):
        #test help subcommand (need to hijack stderr
        with NoStdStreams():
            args = ['gittkt.py','pull','help']
            retval = gittkt.Main(args)
        #******  SETUP  ******
        #make a file in master
        file = open('temp.txt','w')
        file.write("some text")
        file.close()
        #for some reason,t he -a optio of commit didn't work, so this add is
        #needed
        gitshelve.git('add','temp.txt')
        gitshelve.git('commit','-m','some file')

        #create some tickets
        args = ['gittkt.py','new']
        args.extend(self.GetFieldArgs())
        retval = gittkt.Main(args)

        args = ['gittkt.py','new']
        args.extend(self.GetFieldArgs({'name':'different'}))
        retval = gittkt.Main(args)

        args = ['gittkt.py','new']
        args.extend(self.GetFieldArgs({'name':'a_third'}))
        retval = gittkt.Main(args)

        #clone the repository with the default gittkt branch
        remoteRepoParent = None
        try:
            localRepoDir = os.path.abspath(os.getcwd())
            repoName = os.path.basename(localRepoDir)
            remoteRepoParent = tempfile.mkdtemp()
            remoteRepoDir = os.path.join(remoteRepoParent,repoName)
            gitshelve.git('clone',localRepoDir,remoteRepoDir)
            os.chdir(remoteRepoDir)
            gitshelve.git('branch',gittkt.GIT_TKT_DEFAULT_BRANCH,
                          'origin/%s'%gittkt.GIT_TKT_DEFAULT_BRANCH)
                          
        except Exception as e:
            os.chdir(localRepoDir)
            if remoteRepoParent:
                shutil.rmtree(remoteRepoParent)
            raise
        #create some new tickets in both repositories
        args = ['gittkt.py','new']
        args.extend(self.GetFieldArgs({'name':'remoteTicket'}))
        retval = gittkt.Main(args)

        args = ['gittkt.py','new']
        args.extend(self.GetFieldArgs({'name':'remoteTicket'}))
        retval = gittkt.Main(args)

        os.chdir(localRepoDir)
        args = ['gittkt.py','new']
        args.extend(self.GetFieldArgs({'name':'remoteTicket'}))
        retval = gittkt.Main(args)
        #******END SETUP******
        args = ['gittkt.py','pull',remoteRepoDir]
        retval = gittkt.Main(args)
        """
        """
        self.assertRegexpMatches(retval,'.*local changes after remote'
            '.*\nAdded remotely: #4'
            '.*\nAdded remotely: #5'
            '.*\nAdded locally: #6 \[changed from #4\]'
            )

        args = ['gittkt.py','pull','--keep-local',remoteRepoDir]
        retval = gittkt.Main(args)
        self.assertRegexpMatches(retval,'.*remote changes after local'
            '.*\nAdded locally: #4'
            '.*\nAdded remotely: #5 \[changed from #4\]'
            '.*\nAdded remotely: #6 \[changed from #5\]'
            )

        #cleanup
        os.chdir(localRepoDir)
        shutil.rmtree(remoteRepoDir)

    def testArchive(self):
        #TODO: once arechiving is implmented, we need to update the
        #testPull case to test that archived tickets are merged properly
        t = gittkt.GitTkt()
        t.archive(1)

    def testEdit(self):
        #test help subcommand (need to hijack stderr
        with NoStdStreams():
            args = ['gittkt.py','edit','help']
            retval = gittkt.Main(args)

        args = ['gittkt.py','new']
        args.extend(self.GetFieldArgs())
        retval = gittkt.Main(args)

        localId,uuid = self.GetAddedTicketIds(retval)
        args = ['gittkt.py','--non-interactive','edit',localId]
        args.extend(self.GetFieldArgs({'name':'edited'}))
        retval = gittkt.Main(args)
        self.assertRegexpMatches(retval,"Successfully edited ticket #1")
        data = gitshelve.git('cat-file','-p',
                '%s:%s'%(gittkt.GIT_TKT_DEFAULT_BRANCH, "active/%s"%uuid))
        self.assertRegexpMatches(data,"'name': 'edited'")

        args = ['gittkt.py','--non-interactive','edit',uuid]
        retval = gittkt.Main(args)

        args = ['gittkt.py','--non-interactive','edit','100']
        self.assertRaises(gittkt.GitTktError,gittkt.Main,args)

    #-------------------------End unit tests--------------------
    def setUp(self):
        """Create a new git repository, cd to it, and create the initial 
           commit"""
        self.gitDir = tempfile.mkdtemp()
        self.lastCWD = os.getcwd()
        os.chdir(self.gitDir)
        gitshelve.git('init')

    def tearDown(self):
        """Delete the git repository"""
        os.chdir(self.lastCWD)
        shutil.rmtree(self.gitDir)

#def suite():
#    return unittest.TestLoader().loadTestsFromTestCase(t_gittkt)

if __name__ == '__main__':
    unittest.main()
