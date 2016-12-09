#!/usr/bin/env python3
#
# Java aplication launcher - proof of concept 
# Authors:  Roman Vais <rvais@redhat.com>
#

import sys              # argumenst accessed by  sys.argv
import os               # environment variables of the shell/machine
import errno            # errno for mkdirs function
import configparser     # ini file parsing module
import subprocess       # for launching another application
import logging          # python logging module

# definiton of variables_______________________________________________________

prog="program"          # any string, used only as declaration
launcher="launcher.py"  # original name of a launcher script
confPrefix="java-launcher/#/conf.ini"
cpGeneratorPath=""      # path to class-path generator

# dictionary containing setting for luncher that will be applied 
cfg={"jvmbinary" : "java",    # JVM binary
     "jvmoptions" : "",       # JVM options
     "applargs" : "",         # Default application arguments
     "mainclass" : "",        # Main class of the application
     "classpath" : "",        # Claspath with individual JAR files
     "abrtflag" : "",         # ABRT integration
     "ignoreuserconfig" : ""  # flag "ignore user settings" (always uses app specific)
    }

# values of environmental variables that we actualy use, initialized empty
env={}

# definiton of functions_______________________________________________________

# print help function 
def help():
    print(sys.argv[0] + "\n" +
          "Java Launcher - Proof of concept script\n" +
          "usage:\t" + sys.argv[0] + " prog\n" +
          "\tprog - name of the program/application you want" +
          "to launch\n", file=sys.stderr)

# taken from stack overflow
# <http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python>
def mkdirs(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

# Logging setup function
def getLogger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s|[%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def getXDGvalues():

    logger = getLogger(launcher);

    # XDG defaults - default values for unset XDG environmental variables
    xdgDef={"HOME" : "./",                      # if no home use PWD 
            "XDG_CONFIG_HOME" : "$HOME/.config",
            "XDG_DATA_HOME" : "$HOME/.local/share",
            "XDG_CACHE_HOME" : "$HOME/.cache",
            "XDG_CONFIG_DIRS" : "/etc/xdg", 
            "XDG_DATA_DIRS" : "/usr/local/share:/usr/share"
           }

    # set the defaults for env
    for key, value in xdgDef.items():
        if (key in os.environ):
            xdgDef[key] = os.environ[key]
  
    for key, value in xdgDef.items():
        paths = value.split(':')
        for i in range(len(paths)):            
            paths[i] = paths[i].replace("$HOME", home)
            paths[i] = paths[i].replace('//', '/')

        value = ':'.join(paths)
        xdgDef[key] = value

        logger.debug("'%s'='%s'", key, env[key])

    return xdgDef

def veryfiAndCorrectXDGcfg(xdg):
    # if xdg configuration was not given, get it directly
    if ((xdg == None) or (not isinstance(xdg,dict))):
        return getXDGvalues()

    somethingMissing = list()
    requredPaths = ["XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME",
                    "XDG_CONFIG_DIRS", "XDG_DATA_DIRS"]
    for key in requredPaths:
        if (not (key in xdg)):
            somethingMissing.append(key)

    if (len(somethingMissing) == 0):
        return xdg

    if (len(somethingMissing) == len(requredPaths)):
        return getXDGvalues()
  
    defaultsXDG = getXDGvalues()
    for (key in somethingMissing):
        xdg[key] = defaultsXDG[key];

    return xdg
    
def getSingileConfigPath(programName, xdgCfg):
    pathSufix = confPrefix.replace('#', programName, 1)
    paths=[]

    if (xdgCfg.find(":") >= 0 ):
        paths.extend(xdgCfg.split(':'))
    else :
        paths.append(xdgCfg)

    for (path in paths):
        filename = os.path.join(env[path, pathSufix)
        if (os.path.exists(filename) and os.path.isfile(filename)):
            return path
    return None

def getEfectiveConfig(programName, xdg=None):
    efectiveConfig = dict()

    xdg = veryfiAndCorrectXDGcfg(xdg)

    # try to find corresponding config files (depth first search basicaly)
    systemCfg = getSingileConfigPath(launcher, '%s:%s' 
        % (xdg["XDG_CONFIG_DIRS"], xdg["XDG_DATA_DIRS"]))
    appGenericCfg = getSingileConfigPath(programName, '%s:%s' 
        % (xdg["XDG_CONFIG_DIRS"], xdg["XDG_DATA_DIRS"]))
    userGenericCfg = getSingileConfigPath(launcher, '%s:%s' 
        % (xdg["XDG_CONFIG_HOME"], xdg["XDG_DATA_HOME"]))
    userAppSpecificCfg = getSingileConfigPath(programName, '%s:%s' 
        % (xdg["XDG_CONFIG_HOME"], xdg["XDG_DATA_HOME"]))

    # create a list with ordering by priority
    # later used will override previous values but cfg comming sooner can stop
    # further processing
    cfgFiles = [systemCfg, appGenericCfg, userGenericCfg, userAppSpecificCfg] 
    
    #logger instance
    logger = getLogger(launcher)

    for (path in cfgFiles):
        if (path == None): # no such config was found, skipping ...
            continue

        #create new instance of ini-file parser (to be safe)
        iniParser = configparser.ConfigParser()
        iniParser.read_file(open(path))

        # store all required vaules, override old ones
        for item, value in iniParser['section'].items():
            efectiveConfig[item] = value.strip('"')

        # print current configuration we have so far
        loggin.debug("File: '" + path + "' included to configuration" )
        for item, value in efectiveConfig.items():
            loggin.debug(item + " = " + value)

        # if processing of config files is supposed to be discontionued
        if (("skipMoreSpecificCfgs" in efectiveConfig) and
            (efectiveConfig["skipMoreSpecificCfgs"] == True)):
            break;

    return efectiveConfig;    

def getClasspathFromCache(progName, xdg=None):
    xdg = veryfiAndCorrectXDGcfg(xdg)    
    cpFile = os.path.join(xdg["XDG_CACHE_HOME"], launcher, "ClasspathCache", (progName + ".cp"))

    if (os.path.exists(cpFile) and os.path.isfile(cpFile)):
        cpFile = open(cpFile, "r") 
        classPath = cpFile.read()

        return classpath

    return None
    

### def walkInDirTree(root="./"):
    

# main_________________________________________________________________________

# set up loggin 
logger = getLogger(launcher)

# get program neame form symbolic link or first argument
arg0 = os.path.basename(sys.argv[0])
print("'" + arg0 + "'")

if (arg0 == launcher or arg0 == ''):
    if (len(sys.argv) <= 1 or 
        (len(sys.argv[1]) <= 0 or sys.argv[1].startswith('-'))):
        help()
        exit(1);
    arg0 = os.path.basename(sys.argv[1])

prog = arg0
logger.debug("Program name resolved: '%s'", prog)

# get efective configuration
efcfg = getEfectiveConfig()
# check if all necesarry configuration is available (validation step)
for item, value in cfg.items():
    if (item.startswith('jvmb') or item.startswith('main') or item.startswith("classpath")):
#    if (item.startswith('jvmb') or item.startswith("classpath")):
        if (value == ''):
            print("Configuration of '" + item + "' is missing for '" + 
                prog + "' application.\n" +
                "There for it is not possible to launch it.", file=sys.stderr)
            exit(2)

###
# MAKE SURE THAT ALL PATHS IN CLASS PATH HAVE BEEN EXPANDED !!! 
# but it is not the buden of a launcher to deal with
###

if (cfg["classpath"] == "dynamic"):
    cfg["classpath"] = getClasspathFromCache(prog)

if (cfg["classpath"] == None):
    #TODO: launching the cp generetor.
    exit(2)

args = [cfg["jvmbinary"], cfg["jvmoptions"], "-classpath", cfg["classpath"], cfg["mainclass"],
        cfg["applargs"]]

#TODO System properties needs to be edited, currently wont work 
if not ('SystemProperties' in efcfg):
    logger.debug("No system properties ... ")
else:
    for prop, value in iniParser['SystemProperties'].items():
        args.insert(4,"-D" + prop + "=" + value)

args = list(filter(None, args))

for string in args:
    sys.stdout.write(string + " ")
sys.stdout.write("\n")
sys.stdout.flush()

# exit(0)
for item in subprocess.run(args).args:
    print("'" + item + "'")

exit(subprocess.run(args).returncode)















