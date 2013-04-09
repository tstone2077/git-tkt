"""
    gittkt library.  See README for more information
"""
#construction of the version information
GITTKT_VERSION="0.1.0"
GITTKT_DEFAULT_BRANCH='git-tkt'
GITTKT_NUM_MAP_FILE='index.txt'
MIN_UUID_LENGTH=30

class GitTkt:
    def __init__(self,branch,non_interactive,save):
        pass
    def run(self,command,printHelpFunc,*args,**kwargs):
        if command == 'help':
            printHelpFunc()
            return 0
        print(command)
        print(args)
        print(kwargs)
        return 0
