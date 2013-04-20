"""
    class used to implement gittkt's interactive shell.
"""
import shlex
import sys

#python 2 and 3 compatibility
try:
    raw_input
except NameError:
    import builtins
    builtins.raw_input = builtins.input
#This is here so we can override raw input during the unit testing
raw_input = raw_input        

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

    def __init__(self,branch,outstream=None):
        self.branch = branch
        if outstream is None:
            outstream = sys.stdout
        self.outstream = outstream
        self.outstream.write("Using branch %s\n"%self.branch)
        self.outstream.write("type 'commands' for a list of commands\n")

    def Help(self,args):
        self.outstream.write(str(args))
        self.outstream.write("\n")

    def Commands(self,args):
        self.outstream.write(str(args))
        self.outstream.write("\n")

    def Exit(self,args):
        self.outstream.write(self.EXIT_STR)
        self.outstream.write("\n")

    def Run(self,parseFunc):
        input = ""
        while input != 'exit':
            input = self.Prompt()
            try:
                args = shlex.split(input)
                if args[0] in self.shellCommands.keys():
                    commandFunc = args[0][0].upper() + args[0][1:]
                    func = getattr(self,commandFunc)
                    func(args[1:])
                else:
                    parsedArgs = parseFunc(shlex.split("git-tkt "+input))
            except Exception as e:
                self.outstream.write(str(e))
                self.outstream.write("\n")

    def Prompt(self):
        self.outstream.write(self.PROMPT)
        return raw_input()
