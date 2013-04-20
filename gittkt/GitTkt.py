"""
    gittkt library.  See README for more information
"""
#construction of the version information
GITTKT_VERSION="0.1.0"
GITTKT_DEFAULT_BRANCH='git-tkt'

from collections import OrderedDict
import gitshelve
import pickle
import re
import sys
from GitTktCache import GitTktCache
from xml.etree import ElementTree

LS_TREE_RE = re.compile('((\d{6}) (tree|blob)) ([0-9a-f]{40})\t(start|(.+))$')
class GitTktError(Exception):pass

class TicketField(object):
    """
    A field that can be stored in the ticket.
    """
    name        = None
    help        = None
    title       = None
    default     = None
    value       = None
    editable    = True
    listColSize = 0
    def __init__(self,name,title,default,help,value=None,editable=True,
                 listColSize = None):
        """
        name = name of the field (e.g. name=status: becomes --status)
        title = title of the field (used in interactive prompts and list 
                table)
        default = default value of the field (used in interactive prompts
                  set if not passed on command line)
        help = help text of the field (used in --help commands)
        value = value of the field (set by the command line parser and used
                in functions so the field data is complete)
        editable = bool to say if this field can be edited or not
        listColSize = if this is a positive integer, this field will be shown in
                      the list command using the number of columns specified
        """
        self.name = name
        self.title = title
        self.default = default
        self.help = help
        self.value = value
        self.editable = editable
        self.listColSize = listColSize

    def SetValue(self,value):
        self.value = value

def GetGitUser():
    return "%s <%s>"%(
        gitshelve.git("config","user.name"),
        gitshelve.git("config","user.email"),
    )

def LoadFields(fieldsFile = None):
    """
    Load the fields that can be stored in a ticket.
    NOTE: the order in which this fields are loaded is the order that they
    are presented in the list and show commands as well as the editable
    display

    Example of fields file:
    <Fields>
        <Field>
            <name>author</name>
            <title>Author</title>
            <help>The author of the ticket</help>
            <default>
                <!-- function is a part of GitTkt class -->
                <call function="GetGitUser" />
            </default>
            <editable>false</editable>
            <listColSize>11</listColSize>
        </Field>
    </Fields>
    """
    fields = OrderedDict()
    if fieldsFile is not None:
        #open and parse the fields file
        root = ElementTree.parse(fieldsFile).getroot()
        for child in root:
            if child.tag.lower() == 'field':
                attribs = {}
                #parse the field tag
                for attrib in child:
                    attribs[attrib.tag] = attrib.text
                    call = attrib.find('.//call')
                    if call is not None:
                        thisModule = sys.modules[__name__]
                        func = getattr(thisModule,call.attrib['function'])
                        attribs[attrib.tag] = func()
                if 'name' not in attribs.keys():
                    raise GitTktError("'name' not found in field list"
                                      " from %s"%fieldsFile)
                fields[attribs['name']] = TicketField(**attribs)
    else:
        #load the default fields
        fields['name'] = TicketField(name = "name",
                    title = "Ticket Name",
                    help = "The name of the ticket",
                    default = "My Ticket",
                    listColSize = 33,
                    )
        fields['description'] = TicketField(name = "description",
                    title = "Description",
                    help = "Description of the ticket",
                    default = "",
                    )
        fields['author'] = TicketField(name = "author",
                    title = "Author",
                    help = "The author of the ticket",
                    default = GetGitUser(),
                    editable = False,
                    listColSize = 11,
                    )
    return fields

class GitTkt(object):
    """ 
    A GitTkt object acts as an interface to a git-tkt system.
    """
    outstream = None
    branch = GITTKT_DEFAULT_BRANCH
    nonInteractive = True
    save = False
    def __init__(self,branch,nonInteractive,save,loadFolders,fields = None,
                 outstream = None):
        if fields is None:
            self.fields = LoadFields()
        else:
            self.fields = fields
        if outstream is None:
            outstream = sys.stdout
        self.outstream = outstream
        self.branch = branch
        self.nonInteractive = nonInteractive
        self.save = save
        self.cache = GitTktCache(loadFolders,self.fields,self.branch,outstream)

    def New(self,*args,**kwargs):
        """
        Create a new ticket.
        """
        data = {}
        for field in self.fields:
            if field.editable and field.value is None:
                if self.nonInteractive:
                    raise GitTktError("ERROR: No value for field set.  to set a"
                                      "value, use --%s."%field.name)
                inputStr = raw_input("%s [%s]: "%(field.title,field.default))
                if len(inputStr) == 0:
                    data[field.name] = field.default
                else:
                    data[field.name] = inputStr
            else:
                data[field.name] = field.value
        data['creation_date'] = str(datetime.datetime.now())
        folder = None
        if 'to_folder' in kwargs:
            folder = kwargs['to_folder']
        ticketId = self.cache.Add(data,folder)

    def Folders(self,*args,**kwargs):
        try:
            data = gitshelve.git('ls-tree','--full-tree',self.branch)
            for line in data.split("\n"):
                matchObj = LS_TREE_RE.match(line)
                if matchObj is not None:
                    self.outstream.write("%s\n"%matchObj.group(5))
            return 0
        except gitshelve.GitError as e:
            self.outstream.write("No folders found.\n")
            return 1

    def Run(self,command,printHelpFunc,*args,**kwargs):
        if len(args) != 0:
            raise GitTktError("function only takes 2 positional arguments")

        if command == 'help':
            printHelpFunc()
            return 0

        command = command[0].upper() + command[1:]
        function = getattr(self,command)
        return function(args,kwargs)


