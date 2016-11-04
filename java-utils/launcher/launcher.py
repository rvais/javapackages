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

# definiton of variables 
cfgFile="jlauncher.cfg.ini"         # default name of config file for launcher
globalCfg="jlauncher/global.ini"
testEnvironment="$HOME/tstenv"      # abs path to dir where to create test env
                                    # if it's not to be used leave empty str

# dictionary containing setting for luncher that will be applied 
cfg={"jvmbinary" : "java",    # JVM binary
     "jvmoptions" : "",       # JVM options
     "applargs" : "",         # Default application arguments
     "mainclass" : "",        # Main class of the application
     "classpath" : "",        # Claspath with individual JAR files
     "abrtflag" : "",         # ABRT integration
     "ignoreuserconfig" : ""  # flag "ignore user settings" (always uses app specific)
}

# name of the program we want to launch
prog="program" 
launcher="launcher.py" # original name of a launcher script

# list of environment variables we are interested in
envList=["HOME", "MAVEN_REPO" , "XDG_DATA_HOME", "XDG_CONFIG_HOME",
         "XDG_CACHE_HOME", "XDG_CONFIG_DIRS", "XDG_DATA_DIRS"] # , ""

# XDG defaults - default values for unset XDG environmental variables
xdgDef={"XDG_DATA_HOME" : "$HOME/.local/share", "XDG_CONFIG_HOME" : "$HOME/.config",
        "XDG_CACHE_HOME" : "$HOME/.cache", "XDG_DATA_DIRS" : "/usr/local/share:/usr/share",
        "XDG_CONFIG_DIRS" : "/etc/xdg", "MAVEN_REPO" : "$HOME/.m2/repository"}

# values of environmental variables that we actualy use
env={}

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

# just to make sure
if not testEnvironment.endswith('/'):
    testEnvironment+='/'

# set the defaults for env
for key in envList:
    if not (key in os.environ):
        env[key] = xdgDef[key]
    else:
        env[key] = os.environ[key]
  
    print("'" + key + "' = '" + env[key] + "'")

home = env["HOME"]
print("home: " + home)

# make sure all paths end with '/' because they are supposed to be directories
# also replace '$HOME' string for actual home path
for key, value in env.items():
    paths = value.split(':')
    for i in range(len(paths)):
        if (testEnvironment != None and len(testEnvironment) > 0 
            and key != 'HOME'):
            
            paths[i] = testEnvironment + paths[i]
        if not paths[i].endswith('/'):
            paths[i] += '/'
        paths[i] = paths[i].replace("$HOME", home)
        paths[i] = paths[i].replace('//', '/')

        if (testEnvironment != None and len(testEnvironment) > 0 ):
            mkdirs(paths[i])

    value = ':'.join(paths)
    env[key] = value

# get program neame form symbolic link
arg0 = os.path.basename(sys.argv[0])
print("'" + arg0 + "'")

if (arg0 == launcher or arg0 == ''):
    if (len(sys.argv) <= 1 or 
        (len(sys.argv[1]) <= 0 or sys.argv[1].startswith('-'))):
        help()
        exit(1);
    arg0 = os.path.basename(sys.argv[1])

prog = arg0

for key, value in env.items():
    print("'" + key + "' = '" + value + "'")

iniParser = configparser.ConfigParser()

# try to locate global configuration
#--------------------------------------------------
# First we should try to locate static global configuration  which should
# be found in XDG_CONFIG_HOME. Defined by the XDG specification, path to 
# this global configuration should be following:
# XDG_CONFIG_HOME/APPLICATION_NAME/CFG_FILE

filename = os.path.join(env["XDG_CONFIG_HOME"], prog, cfgFile)
if (os.path.exists(filename) and os.path.isfile(filename)):
    print("file '" + filename + "' exists")
    iniParser.read_file(open(filename))

    for item, value in iniParser['section'].items():
        cfg[item] = value.strip('"')

    for item, value in cfg.items():
        print(item + " = " + value)

# TODO: later implement search on other paths as well

# try to locate program configuration

# try to locate user's global configuration

# try to locate users' program configuration

# version=$(awk -F "=" '/database_version/ {print $2}' parameters.ini)

# check if all necesarry configuration is available
for item, value in cfg.items():
    if (item.startswith('jvmb') or item.startswith('main') or item.startswith("classpath")):
#    if (item.startswith('jvmb') or item.startswith("classpath")):
        if (value == ''):
            print("Configuration of '" + item + "' is missing for '" + 
                prog + "' application.\n" +
                "There for it is not possible to launch it.", file=sys.stderr)
            exit(2)

args = [cfg["jvmbinary"], cfg["jvmoptions"], "-classpath", cfg["classpath"], cfg["mainclass"],
        cfg["applargs"]]
if not ('SystemProperties' in iniParser):
    print ("No system properties ... ")
else:
    for prop, value in iniParser['SystemProperties'].items():
        args.insert(4,"-D" + prop + "=" + value)

for string in args:
    sys.stdout.write(string + " ")
sys.stdout.write("\n")
sys.stdout.flush()

# exit(0)

exit(subprocess.run(args).returncode)















