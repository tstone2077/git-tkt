#!/usr/bin/env python

#TODO: change print() to logging.<level>
#TODO: Make LoadFields dynamic, so people can customize the fields stored
#TODO: Change input() to support multiple lines for some fields (such as 
#      description)

import os
import argparse
import gitshelve
import json
import sys
import uuid

GIT_TKT_VERSION=0.1
GIT_TKT_DEFAULT_BRANCH='git-tkt'

#python 2 and 3 compatibility
try:
    raw_input
except NameError:
    import builtins
    builtins.raw_input = builtins.input

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

def newTicket(fields,branch = GIT_TKT_DEFAULT_BRANCH):
    """
    Create a new ticket.
    """
    data = {}
    for field in fields:
        if field.value is None:
            inputStr = raw_input("%s [%s]: "%(field.title,field.default))
            if len(inputStr) == 0:
                data[field.name] = field.default
            else:
                data[field.name] = inputStr
        else:
            data[field.name] = field.value
    #store the new data in gitshelve
    shelfData = gitshelve.open(branch=branch)
    uuid._uuid_generate_time = None
    uuid._uuid_generate_random = None
    uuId = str(uuid.uuid4())
    shelfData[uuId] = str(data)
    shelfData.commit("Adding Ticket %s"%uuId)
    shelfData.close()
    print(json.dumps(data))

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

    #____________________________________________
    # Parse the command line
    #____________________________________________
    parseResults = parser.parse_args(sys.argv[1:])
    print(parseResults)
    if parseResults.subparser in ['new']:
        for field in fields:
            value = getattr(parseResults,field.name)
            if value is not None:
                field.setValue(value)

    if parseResults.subparser == 'help':
        parser.print_help()
        sys.exit(0)
    if parseResults.subparser == 'new':
        if parseResults.help:
            newParser.print_help()
            sys.exit(0)
        else:
            newTicket(fields)

if __name__ == '__main__':
    main()
