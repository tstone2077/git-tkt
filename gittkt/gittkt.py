#!/usr/bin/env python

#TODO: change print() to logging.<level>
#TODO: Make LoadFields dynamic, so people can customize the fields stored
#TODO: Change input() to support multiple lines for some fields (such as 
#      description)
#TODO: when giving multiple arguments to show, the first argument is ignored
#      since it is part of the 'help' attribute instead of 'ticketIds'

import os
import argparse
import gitshelve
import json
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
    name    = None
    help    = None
    title   = None
    default = None
    value   = None
    def __init__(self,name,title,default,help,value=None):
        self.name = name
        self.title = title
        self.default = default
        self.help = help
        self.value = value

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
    """
    fields = []
    fields.append(TicketField(name = "name",
                title = "Ticket Name",
                help = "The name of the ticket",
                default = "My Ticket",
                ))
    fields.append(TicketField(name = "description",
                title = "Description",
                help = "Description of the ticket",
                default = "",
                ))
    fields.append(TicketField(name = "author",
                title = "Author",
                help = "The author of the ticket",
                default="",
                value = GetGitUser(),
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
            if field.value is None:
                inputStr = raw_input("%s [%s]: "%(field.title,field.default))
                if len(inputStr) == 0:
                    data[field.name] = field.default
                else:
                    data[field.name] = inputStr
            else:
                data[field.name] = field.value
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

    def show(self,ticketIds):
        shelfData = gitshelve.open(branch=self.branch)
        for ticketId in ticketIds:
            local,uuid = self._GetTicketIds(ticketId)
            if uuid is None:
                raise GitTktError("Ticket not found: %s"%ticketId)
            ticketData = eval(shelfData["active/%s"%uuid])
            print("-"*30)
            print("Ticket %d (%s)"%(local,uuid))
            for key,value in ticketData.items():
                print("  %s = %s"%(key.upper(),value))
            print("-"*30)
            print
        shelfData.close()

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
    showParser = helpSubParsers.add_parser('show',help = 'show information of an existing ticket.')
    showParser.add_argument('help',help = commandHelpMessage,nargs='?')
    showParser.add_argument('ticketId',help = "id of the ticket",nargs='+')

    #____________________________________________
    # Parse the command line
    #____________________________________________
    parseResults = parser.parse_args(sys.argv[1:])
    print(parseResults)
    if parseResults.subparser != 'help':
        for field in fields:
            try:
                value = getattr(parseResults,field.name)
                if value is not None:
                    field.setValue(value)
            except AttributeError:
                pass

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

if __name__ == '__main__':
    main()
