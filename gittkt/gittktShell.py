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

    def run(self,parseFunc):
        input = ""
        while input != 'exit':
            input = self.prompt()
            try:
                args = shlex.split("git-tkt "+input)
                if args[1] in self.shellCommands.keys():
                    func = getattr(self,args[1])
                    func(args)
                else:
                    parsedArgs = parseFunc(shlex.split("git-tkt "+input))
            except Exception as e:
                self.outstream.write(str(e))
                self.outstream.write("\n")

    def prompt(self):
        self.outstream.write(self.PROMPT)
        return raw_input()
