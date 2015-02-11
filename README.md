[![Build Status](https://travis-ci.org/tstone2077/git-tkt.svg?branch=develop)](https://travis-ci.org/tstone2077/git-tkt)
[![Coverage Status](https://coveralls.io/repos/tstone2077/git-tkt/badge.svg)](https://coveralls.io/r/tstone2077/git-tkt)

gittkt is a python based distributed ticketing system.  It was inspired by
the work done within git-issue and git-issius.

Advantages of git tkt:
    * Ticket data is stored on a separate branch, but cached in a sql database.
       This allows for complex queries for the 'list' command.
    * Field information is dynamic.  You can store whatever data you want
       in a ticket.
    * Allows any field to be set via the command line (e.g. --name, --author)
       or interactively.
    * Written as a module and can be used as such.
    * Written for python 2 AND python 3.

Development:
    Usage:
        git tkt (no-options) opens interactive shell
        git tkt help
        git tkt <command> help opens the help information
        global options:
            --branch branchname          use this branch as the shelf
            --non-interactive            do not prompt the user
            --load-folders folder[,folder] load tickets from the given folders
            --fields-file                load this file which contains the field
                                         information
            --save                       save given global options as default
                                         for this git repository
        commands:
            new
                This command creates a new ticket.  If a --<fieldname> is not
                set, then the user enters interactive mode unless the
                --non-interactive option was passed.
                Options:
                    --<fieldname> sets that field data

            show ticketId [ticketId ...]
                show information regarding the specific tickets passed
                Options:
                    --fields=fieldname[,fieldname,...] show only data for those 
                                                       fields
            list
                list the tickets
                Options:
                    --query sql_query send an sql 'WHERE' query to the database
                    --<fieldname>-equals fieldname:value[,fieldname:value]
                        get a list of tickets that have ALL of the equalities
                        passed
                    --<fieldname>-not-equals fieldname:value[,fieldname:value]
                        get a list of tickets that have ALL of the inequalities
                        passed
                    --<fieldname>-like 
                        fieldname:value[,fieldname:value]
                        get a list of tickets that have ALL of like expressions
                        passed.  (Like expressions are SQL like expressions)
                    --<fieldname>-not-like
                        get a list of tickets that have NONE of like expressions
                        passed.  (Like expressions are SQL like expressions)

            edit ticketId [ticketId ...]
                edit fields in the list of tickets passed.  If a fieldname
                option is passed, then all the tickets will be set to that field
                data.  The user will be prompted for any other field that is not
                set unless the --non-interactive option was passed.
                Options:
                    --<fieldname>=value set the value of the field

            pull remote
                Get the latest ticket data from the remote location and merge it
                with the local ticket data.  This is not a typical git merge.
                TODO: More information needs to be given on this.
                Options:
                    --remote-branch the remote ticket branch to pull from
                    --keep-local-index keeps the local indexing and alters the
                                       remote indexes be placed after the local
                                       indexing.
                                       TODO: Give a more info reference.
                
            push remote
                Push the local ticket data up to the remote server
                Options:
                    --remote-branch the remote ticket branch to pull from

            archive ticketId [ticketId ...]
                Move given tickets to the 'archived' folder

            move ticketId newFolder
                Move tickets to a specific Folder.


    Classes:
       TicketFolder:
            Represents a folder that contains tickets.  The only mandatory
            folder is the 'active' folder.  Other folders can be used as the
            user wants.
            For example, they can make an 'archive' folder for all the closed
            tickets, so they do not clutter the active listing.  Or they can
            make an 'version-1.0', 'version-2.0', and 'version-3.0' folder.

            Properities:
                name:        a unique name for this folder. This translates to a
                             directory on the git branch.
                index.txt:   a text file containing a mapping of a local index 
                             number to the universally unique id of the ticket.
                             This allows easy referencing to a ticket, yet lets
                             tickets change correctly within a distributed 
                             system.
            Methods:
                Add(ticketData):
                    Adds a ticket to this folder.  This includes updating the
                    branch with the correct data, updating the index.txt file,
                    and updating the database cache.
                Remove(ticketData):
                    Removes a ticket from this folder.  This includes updating
                    the branch with the correct data, updating the index.txt
                    file, and updating the database cache.
                Update(ticketData):
                    Updates a ticket from this folder.  This includes updating
                    the branch with the correct data, and updating the database 
                    cache.
                Merge():
                    TODO: Update merge function with necessary parameters once
                    they are known.
                    Perform a merge from one branch to another.  This includes
                    intelligently adding and removing tickets and updating the
                    local numbering scheme within the index.txt file.

       TicketField:
            Represents a field for storing ticket information.

            Properties:
                name:           name of the field (e.g. name=status: becomes 
                                --status)
                title:          title of the field (used in interactive prompts
                                and list table)
                default:        default value of the field (set if not passed on
                                command line, used in interactive prompts)
                help:           help text of the field (used in --help commands)
                value:          value of the field (set by the command line
                                parser and used in functions so the field data
                                is complete)
                editable:       bool to say if this field can be edited or not
                listColSize:    if this is a positive integer, this field will
                                be shown in the list command using the number of
                                columns specified
            Methods:
                SetValue(value):
                    Sets the value of the field.

    Storage:
        Ticket data is stored in a collections.OrderedDict.  That data is stored
        on a separate branch as a json dump.
        NOTE: Pickling doesn't work because string data picked in python2.7 
              cannot be unpickled in python 3.  For that reason, json files are
              being used.  This is an area that may need optimizing in the
              future.
        If a cache databased file does not exist, one is created by reading the
        data for the given folders from the ticket branch.  THE TICKET BRANCH 
        IS ALWAYS UPDATED FIRST.  If ever the branch was updated, but the cached
        database file was not (maybe due to a crash), the database file can be
        re-read.

    Development guidelines:
        Coding style:
            * Keep lines within 80 characters
            * Class names and Methods are CamelCase starting with upper case
            * Variables are CamelCase starting with lower case
        Unittests:
            * unit tests are written as t_<pyfile>
            * all functions have at least one separate unit test
            * write tests that reach the highest code coverage

Future:
    TODO: Document how field data is translated into database inserts/queries
    TODO: Need a clean way to set the fields file for a given folder
    TODO: If fields are added or removed, how do we update existing data?
    TODO: Add subcommand for admin tasks such as:
            list dbcache info (file name, size)
            remove a folder (dangerous... maybe)
