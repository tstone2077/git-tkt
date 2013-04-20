from GitTktFolder import GitTktFolder
import sys

GITTKT_DEFAULT_FOLDER = 'active'
class GitTktCache(object):
    gitTktFolders = {}
    def __init__(self, folders, fields, branch, outstream = None):
        if outstream is None:
            outstream = sys.stdout
        if folders is None:
            folders = [GITTKT_DEFAULT_FOLDER]
        for folder in folders:
            self.gitTktFolders[folder] = GitTktFolder(folder,fields,branch,
                outstream)

    def Add(self,ticketData,folder = None):
        if folder is None:
            folder = GITTKT_DEFAULT_FOLDER
        return self.gitTktFolders[folder].Add(ticketData)
            
