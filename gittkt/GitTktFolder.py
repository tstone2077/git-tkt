#!/usr/bin/env python

#TODO: Change input() to support multiple lines for some fields (such as 
#      description)
#TODO: Cache the map
#TODO: support query parameters for the List command
#TODO: use a screen formatting library for the List command

from collections import OrderedDict
import datetime
from difflib import Differ
import gitshelve
import os
import re
import sys
import uuid

try:
    #python 2
    raw_input
except NameError:
    #python 3
    import builtins
    builtins.raw_input = builtins.input

GITTKT_NUM_MAP_FILE='index.txt'
GITTKT_RESERVED_FIELD_NAMES=['uuid','num','creation_date']
MIN_UUID_LENGTH=30

class GitTktFolder(object):
    name  = ""
    fields  = []
    branch  = None
    nextNum = 0
    numMap = None
    outstream = None

    def __init__(self, name, fields, branch, outstream = None):
        self.name = name
        self.fields = fields
        self.branch = branch
        self.outstream = outstream
        if self.outstream is None:
            self.outstream = sys.stdout

    def __GetTicketIds(self,num):
        localNum = None
        ticketId = None
        if len(num) < MIN_UUID_LENGTH: 
            #we can assume this is a not uuid
            searchRE = re.compile("(?P<num>%s)\t(?P<ticketId>.*)"%num)
        else:
            searchRE = re.compile("(?P<num>[0-9]+)\t(?P<ticketId>%s)"%num)

        self.__LoadNumMap()
        if len(self.numMap) > 0:
            matchObj = searchRE.search(self.numMap)
            if matchObj is not None:
                localNum = int(matchObj.group('num'))
                ticketId = matchObj.group('ticketId')
        return localNum,ticketId

    def __LoadNumMap(self):
        if self.numMap is None:
            shelfData = gitshelve.open(branch=self.branch)
            try:
                self.numMap = shelfData[GITTKT_NUM_MAP_FILE]
            except KeyError:
                #reading from the shelf failed, so we have to start new
                self.numMap = ""
            shelfData.close()

    def __AddToNumMap(self,ticketId):
        self.__LoadNumMap()
        
        #attempt to read it from te shelf
        if self.__GetTicketIds(ticketId) == (None,None) and len(self.numMap) > 0:
            lastEntry = self.numMap.split("\n")[-2]
            self.nextNum = int(lastEntry[:lastEntry.find("\t")])
            
        self.nextNum += 1
        self.numMap += "%d\t%s\n"%(self.nextNum,ticketId)
        commitMsg = "Updating map with %d %s"%(self.nextNum, ticketId)
        shelfData = gitshelve.open(branch=self.branch)
        shelfData['%s/%s'%(self.name,GITTKT_NUM_MAP_FILE)] = self.numMap
        shelfData.commit(commitMsg)
        shelfData.close()

    def __SaveToShelf(self,ticketId,data,message):
        if 'uuid' in data:
            del data['uuid']
        if 'num' in data:
            del data['num']
        shelfData = gitshelve.open(branch=self.branch)
        shelfData['active/%s'%ticketId] = str(data)
        shelfData.commit(message)
        shelfData.close()

    def __GetTicketData(self,ticketId):
        local,uuid = self.__GetTicketIds(ticketId)
        if uuid is None:
            raise GitTktError("Ticket not found: %s"%ticketId)
        shelfData = gitshelve.open(branch=self.branch)
        returnData = ticketData = eval(shelfData["active/%s"%uuid])
        returnData['num'] = local
        returnData['uuid'] = uuid
        shelfData.close()
        return returnData
        
    def __MergeLocalNumbers(self,keepLocal = True):
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
        #update numbering
        #attempt to read it from te shelf
        self.__LoadNumMap()
        uuids = {}
        remoteNumMap = gitshelve.git('cat-file','-p',
                            "FETCH_HEAD:%s"%(GitTkt.GITTKT_NUM_MAP_FILE))
        parentRev = gitshelve.git('merge-base','FETCH_HEAD',self.branch)
        ancestorNumMap = gitshelve.git('cat-file','-p',
                            "%s:%s"%(parentRev,GitTkt.GITTKT_NUM_MAP_FILE))

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
        self.outstream.write("Applying %s changes after %s changes\n"%(second,
            first))
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
                self.outstream.write("Removed %sly: #%s (%s)\n"%(first,localId,
                    uuid))
            elif uuid in removals[second].keys():
                self.outstream.write("Removed %sly: #%s (%s)\n"%(second,localId,
                    uuid))
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
                    self.outstream.write("Added %sly: #%s (%s)\n"%(first,
                        localId,uuid))
                    localIdsUsed[localId] = ""
                    lastLocalId = int(localId)
                else:
                    useNewIds = True
                    #this localId has been used.  We need to set it to
                    #the next number
                    lastLocalId += 1
                    self.outstream.write("Added %sly: #%d [changed from #s]"
                        "(%s)\n"%(first, lastLocalId, localId, uuid))
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
                    self.outstream.write("Added %sly: #%s (%s)\n"%(second,
                        localId,uuid))
                    localIdsUsed[localId] = ""
                    lastLocalId = int(localId)
                else:
                    useNewIds = True
                    #this localId has been used.  We need to set it to
                    #the next number
                    lastLocalId += 1
                    self.outstream.write("Added %sly: #%d [changed from #%s]"
                        "(%s)\n"%(second, lastLocalId, localId, uuid))
                    output[uuid] = str(lastLocalId)

    def __MergeFiles(self):
        pass

    def Add(self,ticketData,nonInteractive = False ):
        uuid._uuid_generate_time = None
        uuid._uuid_generate_random = None
        ticketId = str(uuid.uuid4())
        message = "Added Ticket %s"%ticketId
        #ticket = ticketId : ticketData
        #store the new data in gitshelve
        self.__SaveToShelf(ticketId,ticketData,message)
        self.__AddToNumMap(ticketId)
        self.outstream.write("Added Ticket %s"%ticketId)
        return ticketId

    def Show(self,ticketIds):
        """ Writes the ticket data to self.outstream and returns a dictionary
            where the key is the ticketId and the value is a dictionary of field
            value pairs.
        """
        ticketDatas = {}
        for ticketId in ticketIds:
            ticketData = self.__GetTicketData(ticketId)
            ticketDatas[ticketId] = ticketData
            self.outstream.write("-"*30 + "\n")
            self.outstream.write("Ticket %d (%s)\n"%(ticketData['num'],
                                             ticketData['uuid']))
            for key,value in ticketData.items():
                if key != 'num' and key != 'uuid':
                    self.outstream.write("  %s = %s\n"%(key.upper(),value))
        return ticketDatas

    def List(self):
        """ Writes the ticket data to self.outstream and returns a dictionary
            where the key is the column title and the value is a list of ticket
            data for that column.
        """
        self.__LoadNumMap()
        returnData = {}
        tickets = [line.split("\t") 
                    for line in self.numMap.strip().split("\n") 
                    if len(line)>0]
        if len(tickets) == 0:
            return "No Tickets Found"
        #print the columns
        colData = ["#  |"]
        for field in self.fields.values():
            colSize = field.listColSize
            if colSize and colSize > 0:
                returnData[field.title] = []
                colStr = field.title[:colSize].center(colSize) + "|"
                colData.append(colStr)
        self.outstream.write(''.join(colData) + "\n")

        #print the ticket data
        for ticket in tickets:
            num="%s"%(ticket[0])
            ticketData = self.__GetTicketData(ticket[0])
            rowData = [num.ljust(3) + "|"]
            for field in self.fields.values():
                colSize = field.listColSize
                if colSize and colSize > 0:
                    returnData[field.title].append(ticketData[field.name])
                    if ticketData[field.name]:
                        rowData.append((" "+
                            ticketData[field.name][:colSize-2]+
                            " ").ljust(colSize) + "|")
                    else:
                        rowData.append("".ljust(colSize) + "|")
            self.outstream.write(''.join(rowData) + "\n")
        return returnData

    def Edit(self,ticketIds,interactive = True):
        """
            Returns a list of dictionaries where the key is the ticketId and the
            value is a dictionary containing the ticket data (field.name,value)
            Writes to self.outstream
        """
        returnData = {}
        for ticketId in ticketIds:
            ticketData = self.__GetTicketData(ticketId)
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
            self.__SaveToShelf(uuid,ticketData,message)
            returnData[ticketId] = ticketData
            self.outstream.write("Successfully edited ticket #%s\n"%localId)
        return returnData

    def Pull(self,remote,remoteBranch,keepLocal = True):
        gitshelve.git('fetch',remote,remoteBranch)
        self.__mergeLocalNumbers(keepLocal)
        self.__mergeFiles()
