#!/usr/bin/env python

#TODO: change print() to logging.<level>
#TODO: Make LoadFields dynamic, so people can customize the fields stored
#TODO: Change input() to support multiple lines for some fields (such as 
#      description)
#TODO: when giving multiple arguments to show, the first argument is ignored
#      since it is part of the 'help' attribute instead of 'ticketIds'

import argparse
import datetime
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
    listColSize = 0
    interactive = True
    def __init__(self,name,title,default,help,value=None,interactive=True,
                 listColSize = None,order = None):
        """
        name = name of the field (e.g. name=status: becomes --status)
        title = title of the field (used in interactive prompts and list 
                table)
        default = default value of the field (used in interactive prompts
                  set if not passed on command line)
        help = help text of the field (used in --help commands)
        value = value of the field (set by the command line parser and used
                in functions so the field data is complete)
        interactive = bool to say if this field should be interactive or not
        listColSize = if this is a positive integer, this field will be shown in
                      the list command using the number of columns specified
        """
        self.name = name
        self.title = title
        self.default = default
        self.help = help
        self.value = value
        self.interactive = interactive
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
    presented in the list and show commands as well as the interactive display
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
                interactive = False,
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

    def new(self):
        """
        Create a new ticket.
        """
        data = {}
        for field in self.fields:
            if field.interactive and field.value is None:
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
        print("Added Ticket #%d (%s)"%(self.nextNum,ticketId))

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
        shelfData = gitshelve.open(branch=self.branch)
        shelfData['active/%s'%ticketId] = str(data)
        shelfData.commit(message)
        shelfData.close()

    def archive(self,ticketIds):
        #move ticketId from the active directory to the archived
        #archived tickets are not loaded by default.  They can be
        #loaded and queried if needed.
        pass

    def _GetTicketData(self,ticketId,fieldNames = None):
        local,uuid = self._GetTicketIds(ticketId)
        if uuid is None:
            raise GitTktError("Ticket not found: %s"%ticketId)
        shelfData = gitshelve.open(branch=self.branch)
        returnData = ticketData = eval(shelfData["active/%s"%uuid])
        if fieldNames is not None:
            returnData = {}
            for name in fieldNames:
                returnData[name] = ticketData[name]
        returnData['num'] = local
        returnData['uuid'] = uuid
        shelfData.close()
        return returnData
        
    def show(self,ticketIds):
        for ticketId in ticketIds:
            ticketData = self._GetTicketData(ticketId)
            print("-"*30)
            print("Ticket %d (%s)"%(ticketData['num'],ticketData['uuid']))
            for key,value in ticketData.items():
                print("  %s = %s"%(key.upper(),value))
            print("-"*30)
            print

    def list(self):
        #TODO: support query parameters
        #TODO: use a screen formatting library
        self._LoadNumMap()
        tickets = [ line.split("\t") for line in self.numMap.strip().split("\n") ]
        
        #print the columns
        colData = ["#  |"]
        for field in self.fields:
            colSize = field.listColSize
            if colSize > 0:
                colStr = field.title[:colSize].center(colSize) + "|"
                colData.append(colStr)
        print(''.join(colData))

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
            print(''.join(rowData))

def main():
    """
    Function called when this file is called from the command line
    """
    commandHelpMessage = 'show this help message and exit'
    fields = LoadFields()
    versionStr = "%s %s"%(os.path.basename(sys.argv[0]),str(GIT_TKT_VERSION))
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

    #---------------------------------------------
    # help command
    #---------------------------------------------
    helpSubParsers = parser.add_subparsers(dest="subparser",
                                           title="Commands that can be run")

    helpParser = helpSubParsers.add_parser('help',help = commandHelpMessage)

    #---------------------------------------------
    # new command
    #---------------------------------------------
    newParser = helpSubParsers.add_parser('new',help = 'create a new ticket.')
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
    showParser = helpSubParsers.add_parser('show',help = 'show information of'
                                           ' an existing ticket.')
    showParser.add_argument('help',help = commandHelpMessage,nargs='?')
    showParser.add_argument('ticketId',help = "id of the ticket",nargs='+')

    #---------------------------------------------
    # list command
    #---------------------------------------------
    listParser = helpSubParsers.add_parser('list',help = 'display a list of all'
                                           ' the tickets.')
    listParser.add_argument('help',help = commandHelpMessage,nargs='?')

    #____________________________________________
    # Parse the command line
    #____________________________________________
    parseResults = parser.parse_args(sys.argv[1:])

    print(parseResults)
    if parseResults.subparser != 'help':
        for field in fields:
            try:
                value = getattr(parseResults,field.name)
                if field.value is None and not field.interactive:
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
            print("Storing config data: --%s '%s'"%(data,confData[data]))
            with open(gittktConf,'w') as file:
                file.write(str(confData))
    for data in configurableData:
        if "--%s"%data not in sys.argv:
            try:
                print("Using config data: --%s '%s'"%(data,confData[data]))
                setattr(parseResults,data,confData[data])
            except KeyError:
                pass
        
    #---------------------------------
    # Handle parse results
    #---------------------------------
    tkt = GitTkt(fields,parseResults.branch)
    if parseResults.subparser == 'help':
        parser.print_help()
        sys.exit(0)
    if parseResults.subparser == 'new':
        if parseResults.help:
            newParser.print_help()
            sys.exit(0)
        else:
            tkt.new()
    elif parseResults.subparser == 'show':
        if 'help' in parseResults.ticketId:
            showParser.print_help()
            sys.exit(0)
        else:
            tkt.show(parseResults.ticketId)
    elif parseResults.subparser == 'list':
        if parseResults.help:
            listParser.print_help()
            sys.exit(0)
        else:
            tkt.list()

if __name__ == '__main__':
    main()
