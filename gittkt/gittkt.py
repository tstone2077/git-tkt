import argparse
import logging
import os
import shlex
import sys

#python 2 and 3 compatibility
try:
    raw_input
except NameError:
    import builtins
    builtins.raw_input = builtins.input

#construction of the version information
GITTKT_VERSION="0.1.0"
GIT_TKT_DEFAULT_BRANCH='git-tkt'
GIT_TKT_NUM_MAP_FILE='index.txt'
MIN_UUID_LENGTH=30

class ArgParseError(Exception):pass
class GitTktArgParser(argparse.ArgumentParser):
    """
    argument parser that throws exceptions instead of prints to stderr.
    Also subcommands are optional.
    """
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
        raise ArgParseError(message)
        
        
class GitTktShell:
    branch = None
    outstream = None
    PROMPT   = "]>"
    EXIT_STR = "Thank you. Come again."
    shellCommands = {
        'help':'show the help text',
        'commands':'show the command text',
        'exit':'exit the git-tkt shell',
    }

    def __init__(self,branch,outstream=sys.stdout):
        self.branch = branch
        self.outstream = outstream
        self.outstream.write("Using branch %s\n"%self.branch)
        self.outstream.write("type 'commands' for a list of commands\n")

    def help(self,args):
        self.outstream.write(str(args))
        self.outstream.write("\n")

    def commands(self,args):
        self.outstream.write(str(args))
        self.outstream.write("\n")

    def exit(self,args):
        self.outstream.write(self.EXIT_STR)
        self.outstream.write("\n")

    def run(self):
        input = ""
        while input != 'exit':
            input = self.prompt()
            try:
                args = shlex.split("git-tkt "+input)
                if args[1] in self.shellCommands.keys():
                    func = getattr(self,args[1])
                    func(args)
                else:
                    parsedArgs = ParseArgs(shlex.split("git-tkt "+input))
            except Exception as e:
                self.outstream.write(str(e))
                self.outstream.write("\n")

    def prompt(self):
        self.outstream.write(self.PROMPT)
        return raw_input()
        
def GitTkt(parsedArgs,parser):
    """ Run GitTkt command based on the arguments recieved """
    if parsedArgs.subcommand is None:
        if parsedArgs.non_interactive:
            raise GitTktError("No subcommand passed in non-interactive mode")
        else: #no sub command and interactive, so we open the shell
            shell = GitTktShell(parsedArgs.branch)
            shell.run()
    if parsedArgs.subcommand == 'help':
        parser.print_help()
        return 0
    return 0

def ParseArgs(args):
    """ Setup the argument parser and parse the given arguments """
    commandHelpMessage = 'show this help message and exit'
    #fields = LoadFields()
    versionStr = "%s %s"%(os.path.basename(args[0]),str(GITTKT_VERSION))
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
    globalParser.add_argument('--save',help='save the current global options'
                              ' for future commands in the current repository',
                        action = 'store_true',
                        default = False)
    globalParser.add_argument('--branch',help='branch name to store tickets.'
                              '  This branch never needs to be checked out.',
                        default = GIT_TKT_DEFAULT_BRANCH)
    globalParser.add_argument("--non-interactive",
                            help = "prevent a prompt for input when a value is"
                                   " not supplied on the command line",
                            default = False, action = "store_true")
    #---------------------------------------------
    # help command
    #---------------------------------------------
    subParsers = parser.add_subparsers(dest="subcommand",
                                           title="subcommands supported:")

    helpParser = subParsers.add_parser('help',help = commandHelpMessage)
    return(parser.parse_args(args[1:]),parser)


def Main(args):
    """ Function called to parse and execute the command line """
    parseResults,parser = ParseArgs(args)
    level=getattr(logging,parseResults.verbose.upper())
    format='%(asctime)s:[%(filename)s(%(lineno)d)]:[%(levelname)s]: %(message)s'
    logging.basicConfig(level=level,format=format)
    logging.debug(parseResults)
    #make sure the return value of GitTkt is an int (return code)
    return int(GitTkt(parseResults,parser))

def EntryPoint():
    """ Function used in setuptools to execute the main CLI """
    showTraceback = False
    if '--show-traceback' in sys.argv:
        showTraceback = True
        del sys.argv[sys.argv.index('--show-traceback')]
    try:
        sys.exit(Main(sys.argv))
    except Exception as e:
        if showTraceback:
            raise
        print("ERROR: %s"%str(e))

if __name__ == '__main__':
    EntryPoint()
