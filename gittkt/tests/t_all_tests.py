import unittest
import sys
import os
dirName = os.path.dirname(__file__)
parentDir = (os.path.abspath(os.path.join(dirName,"..")))
sys.path.insert(0,parentDir)

testModules = ['t_gittktCLI',
               't_gitshelve',
               't_gittkt',
               't_gittktShell',
              ]

suite = unittest.TestSuite()

for t in testModules:
    try:
        # If the module defines a suite() function, call it to get the suite.
        mod = __import__(t, globals(), locals(), ['suite'])
        suitefn = getattr(mod, 'suite')
        suite.addTest(suitefn())
    except (ImportError, AttributeError):
        # else, just load all the test cases from the module.
        suite.addTest(unittest.defaultTestLoader.loadTestsFromName(t))

if __name__ == '__main__':
    print("Python %s"%sys.version)
    unittest.TextTestRunner().run(suite)
