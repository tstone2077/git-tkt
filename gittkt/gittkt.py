#!/usr/bin/env python

#TODO: change print() to logging.<level>
#TODO: Make LoadFields dynamic, so people can customize the fields stored
#TODO: Change input() to support multiple lines for some fields (such as 
#      description)
#TODO: when giving multiple arguments to show, the first argument is ignored
#      since it is part of the 'help' attribute instead of 'ticketIds'
#TODO: Instead of using outputStr, pass in a stream that cna be written to

import argparse
from collections import OrderedDict
import datetime
from difflib import Differ
import gitshelve
import json
import os
import re
import sqlite3
import sys
import uuid

GIT_TKT_VERSION=0.1
GIT_TKT_DEFAULT_BRANCH='git-tkt'
GIT_TKT_NUM_MAP_FILE='numbers.txt'
MIN_UUID_LENGTH=30

#python 2 and 3 compatibility
try:
    raw_input
except NameError:
    import builtins
    builtins.raw_input = builtins.input

class GitTktError(Exception):pass

class TicketField:
    """
    A field that can be stored in the ticket.
    """
    name        = None
    help        = None
    title       = None
    default     = None
    value       = None
    editable    = True
    listColSize = 0
    def __init__(self,name,title,default,help,value=None,editable=True,
                 listColSize = None):
        """
        name = name of the field (e.g. name=status: becomes --status)
        title = title of the field (used in interactive prompts and list 
                table)
        default = default value of the field (used in interactive prompts
                  set if not passed on command line)
        help = help text of the field (used in --help commands)
        value = value of the field (set by the command line parser and used
                in functions so the field data is complete)
        editable = bool to say if this field can be edited or not
        listColSize = if this is a positive integer, this field will be shown in
                      the list command using the number of columns specified
        """
        self.name = name
        self.title = title
        self.default = default
        self.help = help
        self.value = value
        self.editable = editable
        self.listColSize = listColSize

    def setValue(self,value):
        self.value = value

def GetGitUser():
    return "%s <%s>"%(
        gitshelve.git("config","user.name"),
        gitshelve.git("config","user.email"),
    )

def LoadFields():
    """
    Load the fields that can be stored in a ticket.
    NOTE: the order in which this fields are loaded is the order that they are
    presented in the list and show commands as well as the editable display
    """
    fields = []
    fields.append(TicketField(name = "name",
                title = "Ticket Name",
                help = "The name of the ticket",
                default = "My Ticket",
                listColSize = 33,
                ))
    fields.append(TicketField(name = "description",
                title = "Description",
                help = "Description of the ticket",
                default = "",
                ))
    fields.append(TicketField(name = "author",
                title = "Author",
                help = "The author of the ticket",
                default = GetGitUser(),
                editable = False,
                listColSize = 11,
                ))
    return fields

class GitTkt:
    fields  = []
    branch  = GIT_TKT_DEFAULT_BRANCH
    nextNum = 0
    numMap = None

    def __init__(self, fields = None, branch = None):
        if fields is not None:
            self.fields = fields
        if branch is not None:
            self.branch = branch

    def new(self,nonInteractive = False ):
        """
        Create a new ticket.
        """
        data = {}
        for field in self.fields:
            if field.editable and field.value is None:
                if nonInteractive:
                    raise GitTktError("ERROR: No value for field set.  to set a"
                                      "value, use --%s."%field.name)
                inputStr = raw_input("%s [%s]: "%(field.title,field.default))
                if len(inputStr) == 0:
                    data[field.name] = field.default
                else:
                    data[field.name] = inputStr
            else:
                data[field.name] = field.value
        data['creation_date'] = str(datetime.datetime.now())
        uuid._uuid_generate_time = None
        uuid._uuid_generate_random = None
        ticketId = str(uuid.uuid4())
        message = "Added Ticket %s"%ticketId
        #ticket = ticketId : data
        #store the new data in gitshelve
        self._SaveToShelf(ticketId,data,message)
        self._AddToNumMap(ticketId)
        self._UpdateDatabase(ticketId,data)
        return "Added Ticket #%d (%s)"%(self.nextNum,ticketId)

    def _GetTicketIds(self,num):
        localNum = None
        ticketId = None
        if len(num) < MIN_UUID_LENGTH: 
            #we can assume this is a not uuid
            searchRE = re.compile("(?P<num>%s)\t(?P<ticketId>.*)"%num)
        else:
            searchRE = re.compile("(?P<num>[0-9]+)\t(?P<ticketId>%s)"%num)

        self._LoadNumMap()
        matchObj = None
        if len(self.numMap) > 0:
            matchObj = searchRE.search(self.numMap)
        if matchObj is not None:
            localNum = int(matchObj.group('num'))
            ticketId = matchObj.group('ticketId')
        return localNum,ticketId

    def _LoadNumMap(self):
        if self.numMap is None:
            shelfData = gitshelve.open(branch=self.branch)
            try:
                self.numMap = shelfData[GIT_TKT_NUM_MAP_FILE]
            except KeyError:
                #reading from the shelf failed, so we have to start new
                self.numMap = ""
            shelfData.close()

    def _AddToNumMap(self,ticketId):
        #TODO: Cache the map
        self._LoadNumMap()
        
        #attempt to read it from te shelf
        if self._GetTicketIds(ticketId) == (None,None) and len(self.numMap) > 0:
            lastEntry = self.numMap.split("\n")[-2]
            self.nextNum = int(lastEntry[:lastEntry.find("\t")])
            
        self.nextNum += 1
        self.numMap += "%d\t%s\n"%(self.nextNum,ticketId)
        commitMsg = "Updating map with %d %s"%(self.nextNum, ticketId)
        shelfData = gitshelve.open(branch=self.branch)
        shelfData[GIT_TKT_NUM_MAP_FILE] = self.numMap
        shelfData.commit(commitMsg)
        shelfData.close()

    def _UpdateDatabase(self,ticketId,data):
        #update the in memory sqlite3 database for faster queries
        pass

    def _SaveToShelf(self,ticketId,data,message):
        if data.has_key('uuid'):
            del data['uuid']
        if data.has_key('num'):
            del data['num']
        shelfData = gitshelve.open(branch=self.branch)
        shelfData['active/%s'%ticketId] = str(data)
        shelfData.commit(message)
        shelfData.close()

    def archive(self,ticketIds):
        #move ticketId from the active directory to the archived
        #archived tickets are not loaded by default.  They can be
        #loaded and queried if needed.
        pass

    def _GetTicketData(self,ticketId):
        local,uuid = self._GetTicketIds(ticketId)
        if uuid is None:
            raise GitTktError("Ticket not found: %s"%ticketId)
        shelfData = gitshelve.open(branch=self.branch)
        returnData = ticketData = eval(shelfData["active/%s"%uuid])
        returnData['num'] = local
        returnData['uuid'] = uuid
        shelfData.close()
        return returnData
        
    def show(self,ticketIds):
        outputStr = ""
        for ticketId in ticketIds:
            ticketData = self._GetTicketData(ticketId)
            outputStr += "-"*30 + "\n"
            outputStr += "Ticket %d (%s)\n"%(ticketData['num'],
                                             ticketData['uuid'])
            for key,value in ticketData.items():
                if key != 'num' and key != 'uuid':
                    outputStr += "  %s = %s\n"%(key.upper(),value)
            outputStr += "-"*30 + "\n"
        return outputStr

    def list(self):
        #TODO: support query parameters
        #TODO: use a screen formatting library
        self._LoadNumMap()
        outputStr = ""
        tickets = [line.split("\t") 
                    for line in self.numMap.strip().split("\n") 
                    if len(line)>0]
        if len(tickets) == 0:
            return "No Tickets Found"
        #print the columns
        colData = ["#  |"]
        for field in self.fields:
            colSize = field.listColSize
            if colSize > 0:
                colStr = field.title[:colSize].center(colSize) + "|"
                colData.append(colStr)
        outputStr += ''.join(colData) + "\n"

        #print the ticket data
        for ticket in tickets:
            num="%s"%(ticket[0])
            ticketData = self._GetTicketData(ticket[0])
            rowData = [num.ljust(3) + "|"]
            for field in self.fields:
                colSize = field.listColSize
                if colSize > 0:
                    if ticketData[field.name]:
                        rowData.append((" "+
                            ticketData[field.name][:colSize-2]+
                            " ").ljust(colSize) + "|")
                    else:
                        rowData.append("".ljust(colSize) + "|")
            outputStr += ''.join(rowData) + "\n"
        return outputStr

    def edit(self,ticketIds,interactive = True):
        outputStr = ""
        for ticketId in ticketIds:
            ticketData = self._GetTicketData(ticketId)
            localId = ticketData['num']
            uuid = ticketData['uuid']
            for field in self.fields:
                try:
                    currentValue = ticketData[field.name]
                except KeyError:
                    currentValue = field.default
                if field.value is None:
                    if interactive and field.editable:
                        inputStr = raw_input("%s [%s]: "%(field.title,currentValue))
                        if len(inputStr) != 0:
                            ticketData[field.name] = inputStr
                else:
                    ticketData[field.name] = field.value
            message = "Editing ticket %s"%uuid
            self._SaveToShelf(uuid,ticketData,message)
            outputStr += "Successfully edited ticket #%s\n"%localId
        return outputStr

    def pull(self,remote,remoteBranch,keepLocal = True):
        """
        algorithm for merging local number ids:
        when merging, 3 changes can happen:
        1. item added: can be added at the end and renumbered accordingly
        2. item removed (archived or un-archived):can be removed numbers not
                reused unless it was the last item
        3. item changed: happens if a renumbering occurred, in which the same
                rules as added can apply

        so, we want to fetch the latest from the remote.  This will then be
        set to FETCH_HEAD.
        From that point, we can preform a 3-way merge.  We diff the common 
        ancestor with the 2 changed (FETCH_HEAD and self.branch).  This can
        give us a list of added, removed, and changed

        With that list, we can remove everything that needs to be removed from
        the ancestor.  The user can determine if they want the remote numbering
        to change or local numbering to change.  Either way, we can then add 
        the new tickets to the end, ensuring that niether uuids or local ids
        are duplicated.  

        The result should be a merged list with tickets from both branches and
        a new local numbering scheme based on the numbering scheme the user
        wanted to keep.
        """
        outputStr = ""
        gitshelve.git('fetch',remote,remoteBranch)
        #update numbering
        #attempt to read it from te shelf
        self._LoadNumMap()
        uuids = {}
        remoteNumMap = gitshelve.git('cat-file','-p',
                            "FETCH_HEAD:%s"%(GIT_TKT_NUM_MAP_FILE))
        parentRev = gitshelve.git('merge-base','FETCH_HEAD',self.branch)
        ancestorNumMap = gitshelve.git('cat-file','-p',
                            "%s:%s"%(parentRev,GIT_TKT_NUM_MAP_FILE))

        localLines = self.numMap.split("\n")
        remoteLines = remoteNumMap.split("\n")
        ancestorLines = ancestorNumMap.split("\n")

        diff = Differ()
        #find the differences
        localChanges=[x for x in list(diff.compare(ancestorLines,localLines))
                        if x[0] == '+' or x[0] =='-']
        remoteChanges=[x for x in list(diff.compare(ancestorLines,remoteLines))
                        if x[0] == '+' or x[0] =='-']
        #assume we keep remote numbering and alter local numbering
        firstChanges = remoteChanges
        secondChanges = localChanges
        first = 'remote'
        second = 'local'
        if keepLocal:
            first = 'local'
            second = 'remote'
            firstChanges = localChanges
            secondChanges = remoteChanges
        outputStr += "Applying %s changes after %s changes\n"%(second,first)
        #determine the changes that will be needed
        removals = {}
        removals['local'] = OrderedDict()
        removals['remote'] = OrderedDict()
        additions = {}
        additions['local'] = OrderedDict()
        additions['remote'] = OrderedDict()
        ancestor = OrderedDict()
        for line in ancestorNumMap.split("\n"):
            if len(line) > 0:
                ancestor[line.split('\t')[1]] = line.split('\t')[0]
            elif line[0] == '+' and len(line) > 2: #this is an addition
                additions[line[2:].split('\t')[1]] = line[2:].split('\t')[0]
        for line in firstChanges:
            if line[0] == '-' and len(line) > 2: #this is a removal
                removals[first][line[2:].split('\t')[1]] = line[2:].split('\t')[0]
            elif line[0] == '+' and len(line) > 2: #this is an addition
                additions[first][line[2:].split('\t')[1]] = line[2:].split('\t')[0]
        for line in secondChanges:
            if line[0] == '-' and len(line) > 2: #this is a removal
                removals[second][line[2:].split('\t')[1]] = line[2:].split('\t')[0]
            elif line[0] == '+' and len(line) > 2: #this is an addition
                additions[second][line[2:].split('\t')[1]] = line[2:].split('\t')[0]
        #apply the changes
        output = OrderedDict()
        localIdsUsed = {}
        maxValues = max(additions[first].values(),additions[second].values())
        lastLocalId = 0#int(max(maxValues))
        for uuid,localId in ancestor.items():
            if uuid in removals[first].keys():
                outputStr += "Removed %sly: #%s (%s)\n"%(first,localId,uuid)
            elif uuid in removals[second].keys():
                outputstr += "Removed %sly: #%s (%s)\n"%(second,localId,uuid)
            else:
                output[uuid] = localId
                localIdsUsed[localId] = ""
                lastLocalId = int(localId)
        useNewIds = False
        for uuid,localId in additions[first].items():
            if uuid not in ancestor.keys() and \
               uuid not in removals[first].keys() and \
               uuid not in removals[second].keys() and \
               uuid not in output.keys():
                if not useNewIds and localId not in localIdsUsed.keys():
                    #we can use this id
                    output[uuid] = localId
                    outputStr += "Added %sly: #%s (%s)\n"%(first,localId,uuid)
                    localIdsUsed[localId] = ""
                    lastLocalId = int(localId)
                else:
                    useNewIds = True
                    #this localId has been used.  We need to set it to
                    #the next number
                    lastLocalId += 1
                    outputStr += "Added %sly: #%d [changed from #s] (%s)\n"%(
                                    first, lastLocalId, localId, uuid)
                    output[uuid] = str(lastLocalId)
        useNewIds = False
        for uuid,localId in additions[second].items():
            if uuid not in ancestor.keys() and \
               uuid not in removals[first].keys() and \
               uuid not in removals[second].keys() and \
               uuid not in output.keys():
                if not useNewIds and localId not in localIdsUsed.keys():
                    #we can use this id
                    output[uuid] = localId
                    outputStr += "Added %sly: #%s (%s)\n"%(second,localId,uuid)
                    localIdsUsed[localId] = ""
                    lastLocalId = int(localId)
                else:
                    useNewIds = True
                    #this localId has been used.  We need to set it to
                    #the next number
                    lastLocalId += 1
                    outputStr += "Added %sly: #%d [changed from #%s] (%s)\n"%(
                                 second, lastLocalId, localId, uuid)
                    output[uuid] = str(lastLocalId)
        return outputStr
            
def Main(args):
    """
    Function called when this file is called from the command line
    """
    commandHelpMessage = 'show this help message and exit'
    fields = LoadFields()
    versionStr = "%s %s"%(os.path.basename(args[0]),str(GIT_TKT_VERSION))
    parser = argparse.ArgumentParser(description='Git ticket tracking system',
                                     version=versionStr)
    #---------------------------------------------
    # Global arguments
    #---------------------------------------------
    parser.add_argument('--save',help='save the current global options for'
                        ' future commands in the current repository',
                        action = 'store_true',
                        default = False)
    parser.add_argument('--branch',help='branch name to store tickets.  This'
                        ' branch never needs to be checked out.',
                        default = GIT_TKT_DEFAULT_BRANCH)
    parser.add_argument("--non-interactive",
                            help = "do not prompt for input if a value is not "
                            "supplied on the command line",
                            default = False, action = "store_true")

    #---------------------------------------------
    # help command
    #---------------------------------------------
    subParsers = parser.add_subparsers(dest="subparser",
                                           title="Commands that can be run")

    helpParser = subParsers.add_parser('help',help = commandHelpMessage)

    #---------------------------------------------
    # new command
    #---------------------------------------------
    newParser = subParsers.add_parser('new',help = 'create a new ticket.')
    for field in fields:
        if not field.default or len(field.default) == 0:
            helpStr = "%s"%(field.help)
        else:
            helpStr = "%s (defaults to %s)"%(field.help,field.default)
        newParser.add_argument("--%s"%field.name,help = helpStr)
    newParser.add_argument('help',help = commandHelpMessage,nargs='?')

    #---------------------------------------------
    # show command
    #---------------------------------------------
    showParser = subParsers.add_parser('show',help = 'show information of'
                                           ' an existing ticket.')
    showParser.add_argument('help',help = commandHelpMessage,nargs='?')
    showParser.add_argument('ticketId',help = "id of the ticket",nargs='+')

    #---------------------------------------------
    # list command
    #---------------------------------------------
    listParser = subParsers.add_parser('list',help = 'display a list of all'
                                           ' the tickets')
    listParser.add_argument('help',help = commandHelpMessage,nargs='?')

    #---------------------------------------------
    # edit command
    #---------------------------------------------
    editParser = subParsers.add_parser('edit',help = 'edit a specific ticket')
    for field in fields:
        if field.editable:
            editParser.add_argument("--%s"%field.name,help = field.help)
    editParser.add_argument('help',help = commandHelpMessage,nargs='?')
    editParser.add_argument('ticketId',help = "id of the ticket",nargs='+')

    #---------------------------------------------
    # pull command
    #---------------------------------------------
    pullParser = subParsers.add_parser('pull',help = "fetch and merge tickets"
        " from a remote repository.  By default, the remote numbering scheme is"
        " used, so local tickets added will be re-numbered")
    pullParser.add_argument('--remoteBranch',
                            help = 'name of the remote ticket branch')
    pullParser.add_argument('--keep-local',
                            action = 'store_true',
                            default = False,
                            help = 'keep the numbering scheme of the local tickets and apply the remote tickets on top')
    pullParser.add_argument('help',help = commandHelpMessage,nargs='?')
    pullParser.add_argument('remote',help = "name of the remote repository",nargs=1)

    outputStr = ""
    #____________________________________________
    # Parse the command line
    #____________________________________________
    parseResults = parser.parse_args(args[1:])

    if parseResults.subparser != 'help':
        for field in fields:
            try:
                value = getattr(parseResults,field.name)
                if field.value is None and not field.editable:
                    value = field.default
                if value is not None:
                    field.setValue(value)
            except AttributeError:
                pass

    #----------------------------------
    # Read/write config file
    #---------------------------------
    gitRoot = gitshelve.git('rev-parse','--show-toplevel')
    gitDir = os.path.join(gitRoot,'.git')
    if os.path.isfile(gitDir):
        #the repo was created with --separate-git-dir
        with open(gitDir,'r') as file:
           gitDir = file.read().split('gitdir: ')[1].strip()
    
    gittktConfDir = os.path.join(gitDir,'gittkt')
    if not os.path.isdir(gittktConfDir):
        os.makedirs(gittktConfDir)

    gittktConf = os.path.join(gittktConfDir,'config')
    confData = {}
    if os.path.isfile(gittktConf):
        with open(gittktConf,'r') as file:
            try:
                confData = eval(file.read())
            except SyntaxError:
                confData = {}
    configurableData = ['branch']
    if parseResults.save:
        for data in configurableData:
            value = getattr(parseResults,data)
            confData[data] = value
            outputStr += "Storing config data: --%s '%s'\n"%(data,
                         confData[data])
            with open(gittktConf,'w') as file:
                file.write(str(confData))
    for data in configurableData:
        if "--%s"%data not in args:
            try:
                outputStr += "Using config data: --%s '%s'\n"%(data,
                             confData[data])
                setattr(parseResults,data,confData[data])
            except KeyError:
                pass
        
    #---------------------------------
    # Handle parse results
    #---------------------------------
    tkt = GitTkt(fields,parseResults.branch)
    if parseResults.subparser == 'help':
        parser.print_help()
        return 0
    if parseResults.subparser == 'new':
        if parseResults.help and 'help' in parseResults.help:
            newParser.print_help()
            return 0
        else:
            return outputStr + tkt.new(parseResults.non_interactive)
    elif parseResults.subparser == 'show':
        #since there are multiple positional arguments, help may not
        #be present.
        if parseResults.help and 'help' in parseResults.help or \
            'help' in parseResults.ticketId:
            showParser.print_help()
            return 0
        else:
            return outputStr + tkt.show(parseResults.ticketId)
    elif parseResults.subparser == 'list':
        if parseResults.help and 'help' in parseResults.help:
            listParser.print_help()
            return 0
        else:
            return outputStr + tkt.list()
    elif parseResults.subparser == 'edit':
        if parseResults.help and 'help' in parseResults.help or \
            'help' in parseResults.ticketId:
            editParser.print_help()
            return 0
        else:
            return outputStr + tkt.edit(parseResults.ticketId, 
                            not parseResults.non_interactive)
    elif parseResults.subparser == 'pull':
        if parseResults.help and 'help' in parseResults.help or \
            'help' in parseResults.remote:
            pullParser.print_help()
            return 0
        else:
            if not parseResults.remoteBranch:
                parseResults.remoteBranch = parseResults.branch
            return outputStr + tkt.pull(parseResults.remote[0],
                            parseResults.remoteBranch,
                            parseResults.keep_local)

def EntryPoint():
    try:
        retval = Main(sys.argv)
        if isinstance(retval,str) or \
           isinstance(retval,unicode) and \
           len(retval) > 0:
            print(retval)
            sys.exit(0)
        if isinstance(retval,int):
            sys.exit(retval)
        else:
            raise GitTktError("Unknown return type from Main()")
    except Exception as e:
        print("ERROR: %s"%str(e))

if __name__ == '__main__':
    EntryPoint()
