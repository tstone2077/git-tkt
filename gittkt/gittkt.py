#!/usr/bin/env python
import sys
import gitshelve
import argparse

GIT_TKT_VERSION=0.1

class TicketField:
    """
    A field that can be stored in the ticket.
    """
    name = None
    help = None
    def __init__(self,name,title,help):
        self.name = name
        self.aliases = []
        self.help = help

def LoadFields():
    """
    Load the fields that can be stored in a ticket.
    """
    fields = []
    fields.append(TicketField(name = "name",
                title = "Ticket Name",
                help = "The name of the ticket",
                ))
    return fields

def main():
    """
    Function called when this file is called from the command line
    """
    fields = LoadFields()
    parser = argparse.ArgumentParser(description='Git ticket tracking system')
    parser.add_argument('--branch',help='Branch name to store tickets.  This'
                        ' branch never needs to be checked out.')

    parser.parse_args(sys.argv[1:])


if __name__ == '__main__':
    main()
