"""
    gittkt library.  See README for more information
"""
#construction of the version information
GITTKT_VERSION="0.1.0"
GITTKT_DEFAULT_BRANCH='git-tkt'
GITTKT_DEFAULT_SHELF='active'
GITTKT_NUM_MAP_FILE='index.txt'
MIN_UUID_LENGTH=30

import gitshelve
import re
import sys

LS_TREE_RE = re.compile('((\d{6}) (tree|blob)) ([0-9a-f]{40})\t(start|(.+))$')
class GitTktError(Exception):pass

class GitTkt:
    """ 
    A GitTkt object acts as an interface to a git-tkt system.
    """
    def __init__(self,branch,non_interactive,save,loadShelves,fieldsFile = None,
                 outstream = None):
        if outstream is None:
            outstream = sys.stdout
        self.outstream = outstream
        self.branch = branch
        self.non_interactive = non_interactive
        self.save = save
        self.loadShelves = loadShelves

    def archives(self,*args,**kwargs):
        """
        """
        try:
            data = gitshelve.git('ls-tree','--full-tree',self.branch)
            for line in data.split("\n"):
                matchObj = LS_TREE_RE.match(line)
                if matchObj is not None:
                    self.outstream.write("%s\n"%matchObj.group(5))
            return 0
        except gitshelve.GitError as e:
            self.outstream.write("No archives found.\n")
            return 1

    def run(self,command,printHelpFunc,*args,**kwargs):
        if len(args) != 0:
            raise GitTktError("function only takes 2 positional arguments")

        if command == 'help':
            printHelpFunc()
            return 0

        function = getattr(self,command)
        return function(args,kwargs)
