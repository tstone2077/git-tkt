"""
    Command line interface to the gittkt library.

    This file uses a modified argparse.ArgumentParser class to support having
    optional subcommands ('gittktCLI.py' works as well as 'gittktCLI.py list')

    It uses an EntryPoint function as the main function called by setuptools.
    The Main function takes the command line arguments as a parameter to allow
    for unit tests.  It then calls either the interacive shell or the gittkt
    library.
"""
import argparse
import GitTkt
from GitTktShell import GitTktShell
import logging
import os
import sys

class ArgParseError(Exception):pass
class GitTktArgParser(argparse.ArgumentParser):
    """
    argument parser that throws exceptions instead of prints to stderr.
    Also subcommands are optional.
    """
    def __init__(self,ignoreErrors = False,*args,**kwargs):
        self.ignoreErrors = ignoreErrors
        return argparse.ArgumentParser.__init__(self,*args,**kwargs)

    def parse_known_args(self,args=None,namespace=None):
        if args is None:
            args = sys.argv[1:]
        self.args = args
        return argparse.ArgumentParser.parse_known_args(self,args,namespace)

    def error(self,message):
        for action in self._actions:
            if action.dest == 'subcommand' and \
                self._get_value(action,None) == None and \
                message == 'too few arguments':
                return argparse.Namespace()
        if self.ignoreErrors:
            return argparse.Namespace()
        raise ArgParseError(message)
        
def ParseArgs(args):
    """ Setup the argument parser and parse the given arguments """
    commandHelpMessage = 'show this help message and exit'
    #Create a temporary arg parser to get the fields.  These fields are used
    #in the actual argument parser
    tempParser = GitTktArgParser(ignoreErrors = True,add_help = False)
    tempParser.add_argument('--load-fields-file', default = None)
    tempParser.add_argument('extra', nargs="*")
    results = tempParser.parse_args(args[1:])
    fields = GitTkt.LoadFields(results.load_fields_file)
    #dictionary of command to help function of the command.  This is to support
    #help sub-subcommands
    helpFunctions = {}
    versionStr = "%s %s"%(os.path.basename(args[0]),
                          str(GitTkt.GITTKT_VERSION))
    parser = GitTktArgParser(description='git ticket tracking system',
                                     version=versionStr)
    #---------------------------------------------
    # Global arguments
    #---------------------------------------------
    outputParser = parser.add_argument_group("output options")
    outputParser.add_argument("--show-traceback", 
                            action = 'store_true',
                            help="show a traceback message instead of exiting"
                              " gracefully")
    outputParser.add_argument("--verbose", const = "INFO", default = "ERROR",
                            nargs = "?",
                            help="level of verbose output to log"
                            "(DEBUG, INFO, WARNING, ERROR, CRITICAL, FATAL)")

    globalParser = parser.add_argument_group("global options")
    globalParser.add_argument('--branch',help='branch name to store tickets'
                            '(NOTE: This branch never needs to be checked out)',
                            default = GitTkt.GITTKT_DEFAULT_BRANCH)
    globalParser.add_argument("--non-interactive",
                            help = "prevent a prompt for input when a value is"
                                   " not supplied on the command line",
                            default = False, action = "store_true")
    globalParser.add_argument('--save',help='save the current global options'
                            ' for future commands in the current repository',
                            action = 'store_true',
                            default = False)
    globalParser.add_argument('--load-fields-file',
                            help='load xml file containing the field data',
                            default = None)
    globalParser.add_argument('--load-folders',
                            help='comma separated list of folder names to be'
                            ' loaded (use the "folder" command for a listing'
                            ' of names)',
                            default = None)
    #---------------------------------------------
    # help command
    #---------------------------------------------
    subParsers = parser.add_subparsers(dest="subcommand",
                                           title="subcommands supported:")

    helpFunctions['help'] = parser.print_help
    helpParser = subParsers.add_parser('help',help = commandHelpMessage)

    #---------------------------------------------
    # folders command
    #---------------------------------------------
    listFoldersParser = subParsers.add_parser('folders',
                                             help = commandHelpMessage)
    helpFunctions['folders'] = listFoldersParser.print_help

    #---------------------------------------------
    # new command
    #---------------------------------------------
    newParser = subParsers.add_parser('new',help = 'create a new ticket.')
    for field in fields.values():
        if not field.default or len(field.default) == 0:
            helpStr = "%s"%(field.help)
        else:
            helpStr = "%s (defaults to %s)"%(field.help,field.default)
        newParser.add_argument("--%s"%field.name,help = helpStr)
    newParser.add_argument("--to-folder",help = "Add this ticket to the given"
                                                "loaded folder")
    newParser.add_argument('help',help = commandHelpMessage,nargs='?')
    helpFunctions['new'] = newParser.print_help

    parseResults = parser.parse_args(args[1:])
    parseResults.helpFunctions = helpFunctions
    return parseResults,fields

def Main(args):
    """ Function called to parse and execute the command line """
    parseResults,fields = ParseArgs(args)
    level=getattr(logging,parseResults.verbose.upper())
    format='%(asctime)s:[%(filename)s(%(lineno)d)]:[%(levelname)s]: %(message)s'
    logging.basicConfig(level=level,format=format)
    logging.debug(parseResults)
    #make sure the return value of GitTkt is an int (return code)
    if parseResults.subcommand is None:
        shell = GitTktShell(parseResults.branch)
        shell.Run(ParseArgs)
        return 0
    else:
        parseResults = vars(parseResults)
        #show_traceback and verbose have already been used, so we are going
        #to pop them off.
        parseResults.pop('verbose')
        parseResults.pop('show_traceback')
        gitTkt = GitTkt.GitTkt(branch = parseResults.pop('branch'),
                        nonInteractive = parseResults.pop('non_interactive'),
                        save = parseResults.pop('save'),
                        loadFolders = parseResults.pop('load_folders'),
                        fields = fields
                        )
        command = parseResults.pop('subcommand')
        #printHelpFunc = getattr(parser
        helpFunctions = parseResults.pop('helpFunctions')
        return int(gitTkt.Run(command,helpFunctions[command],**parseResults))

def EntryPoint(exit=True):
    """ Function used in setuptools to execute the main CLI """
    showTraceback = False
    if '--show-traceback' in sys.argv:
        showTraceback = True
        del sys.argv[sys.argv.index('--show-traceback')]
    try:
        retval = Main(sys.argv)
        if exit:
            sys.exit(retval)
    except Exception as e:
        if showTraceback:
            raise
        print("ERROR: %s"%str(e))

if __name__ == '__main__':
    EntryPoint()
