"""
    gittkt library.  See README for more information
"""
#construction of the version information
GITTKT_VERSION="0.1.0"
GITTKT_DEFAULT_BRANCH='git-tkt'
GITTKT_DEFAULT_SHELF='active'
GITTKT_NUM_MAP_FILE='index.txt'
MIN_UUID_LENGTH=30

class GitTktError(Exception):pass

class GitTkt:
    def __init__(self,branch,non_interactive,save,listShelves,loadShelves):
        pass
    def run(self,command,printHelpFunc,*args,**kwargs):
        if len(args) != 0:
            raise GitTktError("function only takes 2 positional arguments")
        if command == 'help':
            printHelpFunc()
            return 0
        print(command)
        print(kwargs)
        return 0
