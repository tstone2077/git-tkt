import argparse
import logging
import os
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

def GitTkt(argNamespace):
    """ 
    """
    return 0

def ParseArgs(args):
    """ Setup the argument parser and parse the given arguments """
    commandHelpMessage = 'show this help message and exit'
    #fields = LoadFields()
    versionStr = "%s %s"%(os.path.basename(args[0]),str(GITTKT_VERSION))
    parser = argparse.ArgumentParser(description='git ticket tracking system',
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
    return(parser.parse_args(args[1:]))


def Main(args):
    """ Function called to parse and execute the command line """
    parseResults = ParseArgs(args)
    level=getattr(logging,parseResults.verbose.upper())
    format='%(asctime)s:[%(filename)s(%(lineno)d)]:[%(levelname)s]: %(message)s'
    logging.basicConfig(level=level,format=format)
    logging.debug(parseResults)
    #make sure the return value of GitTkt is an int (return code)
    return int(GitTkt(parseResults))

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
