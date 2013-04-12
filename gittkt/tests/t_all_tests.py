import glob
import os
import sys
import unittest

dirName = os.path.dirname(__file__)
parentDir = (os.path.abspath(os.path.join(dirName,"..")))
if parentDir not in sys.path:
    sys.path.insert(0,parentDir)

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
def SetAllTestsToRun(testModules = None):
    if testModules is None or len(testModules) == 0:
        testModules = [os.path.basename(f)[:-3] for f in glob.glob(os.path.join(
                                                    SCRIPT_DIR,"*.py"))]
        testModules.pop(testModules.index('t_all_tests'))

    suite = unittest.TestSuite()

    print("Running tests from:")
    for t in testModules:
        print(t)
        try:
            #If the module defines a suite() function, call it to get the suite.
            mod = __import__(t, globals(), locals(), ['suite'])
            suitefn = getattr(mod, 'suite')
            suite.addTest(suitefn())
        except (ImportError, AttributeError):
            # else, just load all the test cases from the module.
            t = t.split('.')[0]+"."+t
            suite.addTest(unittest.defaultTestLoader.loadTestsFromName(t))
    return suite

if __name__ == '__main__':
    print("Python %s"%sys.version)
    suite = SetAllTestsToRun(sys.argv[1:])
    unittest.TextTestRunner().run(suite)
