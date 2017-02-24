#!/usr/bin/env python3
#
# Java aplication launcher - proof of concept 
# Authors:  Roman Vais <rvais@redhat.com>
#

import sys              # arguments accessed by  sys.argv
import os               # environment variables of the shell/machine
import errno            # errno for mkdirs function
import subprocess       # for launching another application
import logging          # python logging module
import itertools        # iteration tool of python
import re               # regex

import configparser     # ini file parsing module
import shlex            # unix/shell like sting parser
import pudb             # debuger

# definiton of var & const_____________________________________________
# logging related
loglvl = logging.DEBUG # CRITICAL | ERROR | WARNING | INFO | NOTSET
logname = "launcher.log"

# XDG related
xdg_defaults = {
    "HOME" : "./",      # if no home use PWD 
    "XDG_CONFIG_HOME" : "$HOME/.config",
    "XDG_DATA_HOME" : "$HOME/.local/share",
    "XDG_CACHE_HOME" : "$HOME/.cache",
    "XDG_CONFIG_DIRS" : "/etc/xdg", 
    "XDG_DATA_DIRS" : "/usr/local/share:/usr/share"
}
xdg_cfg = dict()

# class path generator related
cp_gen = None           # path to .py script / executable
cp_gen_module = False   # is imported module that serves as cp gen?

# other
launcher = "launcher"
launcher_py = "launcher.py"
cfg_name = "jlauncher.ini"

halt_launch = False

# efective configuration 
cfg = dict()

# required and optional values idn configuration
cfg_requires = {
    "jvm" : ["jvmBinary", "classPath", "mainClass"] # , "", ""
}

cfg_optional = {
    # "launcher" : ["enableAbrt", "stopFurtherConfigProcessing"]
    "jvm" : ["options"], # , "", ""
    "application" : ["arguments"] 
    
}

# definiton of functions_______________________________________________

def print_help():
    print("help()")



# taken from stack overflow
# <http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python>
def mkdirs(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python > 2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise



def get_ini_parser():
    iniParser = configparser.ConfigParser(empty_lines_in_values=False)
    iniParser.optionxform = str
    return iniParser



def get_logger(name=launcher, level=None, sfx=None):
    if (sfx != None):
        name +=sfx

    logger = logging.getLogger(name)

    if (level != None):
        logger.setLevel(loglvl)

    if (not logger.hasHandlers()): 
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s|[%(levelname)s] %(name)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger



def set_xdg_cfg(xdg_cfg, xdg_key=None, xdg_value=None):
    logger = get_logger()


    # set the defaults for env
    if (xdg_key is None and xdg_value is None):
        for key, value in xdg_defaults.items():
            if (key in os.environ):
                xdg_cfg[key] = os.environ[key]
            else :
                xdg_cfg[key] = xdg_defaults[key]
  
        for key, value in xdg_cfg.items():
            paths = value.split(':')
            for i in range(len(paths)):            
                paths[i] = paths[i].replace("$HOME", xdg_cfg["HOME"])
                paths[i] = paths[i].replace('//', '/')

            value = ':'.join(paths)
            xdg_cfg[key] = value

            logger.debug("'%s' = '%s'", key, xdg_cfg[key])
        return None

    # set specific value, actual value can be None 
    if (xdg_key is not None):
        xdg_cfg[xdg_key] = xdg_value

    return None



def get_config_path(name, xdg_path, filename=cfg_name):
    logger = get_logger()
    paths=[]

    if (xdg_path.find(":") >= 0 ):
        paths.extend(xdg_path.split(':'))
    else :
        paths.append(xdg_path)

    # first depth search
    logger.debug("Looking for following cfg files: ")
    for path in paths:
        f = os.path.join(path, name, filename);
        logger.debug("\t> '%s'", f)
        if (os.path.exists(f) and os.path.isfile(f)):
            logger.debug("\t> '%s' exists!", f)
            return f
   
    logger.debug("No file found!") 
    return None


def parse_cfg_value(value):
    boolean = value.lower();
    if (boolean == "true"):
        value = True

    elif (boolean == "false"):
        value = False

    if (isinstance(value, str)):
        value = shlex.split(value)

    return value



def process_configuration(config_parser, cfg):
    logger = get_logger()

    if (not isinstance(cfg, dict)):
        logger.debug("Variable 'cfg' is not dictionary - overriding.")
        cfg = dict()

    for section in config_parser.sections():
        cfg[section] = dict()
        for option, value in config_parser[section].items():
            value = parse_cfg_value(value)

            # class path has to be garanteed to be expanded
            if (section == "jvm" and option == "classPath"):
                for i, item in enumerate(value):
                    value[i] = os.path.expanduser(value[i])
                    value[i] = os.path.expandvars(value[i])

            cfg[section][option] = value

    return True;



def clone_ini_cfg(source, clone):
    logger = get_logger()
    logger.debug("Clonning configuration.")

    if (not isinstance(clone, dict)):
        logger.debug("Variable 'cfg' is not dictionary - overriding.")
        clone = dict()

    for key, item in source.items():
        if (isinstance(source[key], dict)):
            clone[key] = dict()
            for option, value in source[key].items():
                clone[key][option] = value

        if (isinstance(source[key], list)):
            clone[key] = list()
            for value in source[key].items():
                clone[key].append(value)

        clone[key] = item

    return None



# Merges two processed configurations in a way that values form
# "what" configuration overrides values from "into" configuration.
# @param dictionary with configuration to merge into 
# @param dictioanry with configuration to coppy from
# @param boolean deciding if "into" configuration should be cloned
#        or merged into. If True, duplicate will be created, otherwise
#        it will be merged. Default value is True.
# @param "add or remove" - If True (remove) and value is not defined
#        in "what" but it is defined in "into", than it will be removed
#        from "merge". If False (add) and value is not defined in "into"
#        but is defined in "what", than it is added to "merge".
#        If None than "merge" will be intersection of "what" and "into".
#        Default value is False.
def merge_configuration(into, what, clone=True, aor=False):
    logger = get_logger()

    source = what
    if (clone == True):
        target = dict()
        clone_ini_cfg(into, target) 
        
    else:
        target = into

    if (not isinstance(target, dict) or not isinstance(source, dict)):
        return None

    for key, value in source.items():
        if (key in target and isinstance(source[key], dict)):
            if (not isinstance(target[key], dict) and clone == True):
                target[key] = dict();
                for option, value in source[key].items():
                    target[key][option] = value
            
        if (not key in target and aor == True):
            continue

        if (not isinstance(source[key], dict) or clone == False):
            target[key] = value

    for key, value in target.items():
        if (not key in source and aor == True):
            del target[key]

    return target



def validate_cfg(cfg):
    logger = get_logger()
    logger.info("Validating configuration for required values.")
    cfg_valid = True

    for section, options in cfg_requires.items():
        if ((section not in cfg) or
                (not isinstance(cfg[section], dict))):
            logger.info("Final configuration missing required"
                        + " section '%s'", section)
            cfg_valid = False
            break

        for option in options:
            if (option not in cfg[section]):
                logger.info("Final configuration missing required"
                            + " option '%s' in section '%s'",
                            option, section)
                cfg_valid = False
                break

    if (cfg_valid == False):
        logger.debug(cfg)

        return cfg_valid

    for section, options in cfg_optional.items():
        if ((section not in cfg) or
                (not isinstance(cfg[section], dict))):
            logger.debug("Filling in omitted section '%s' to"
                        + " final configuration", section)
            cfg[section] = dict()

        for option in options:
            if (option not in cfg[section]):
                logger.info("Filling in omitted option '%s' in"
                            + " section '%s'", option, section)
                cfg[section][option] = None

    return True
   


# Main_________________________________________________________________

logging.basicConfig(filename=logname,level=loglvl)
logger = get_logger()

set_xdg_cfg(xdg_cfg);

# get program neame form symbolic link or first argument
arg0 = os.path.basename(sys.argv[0])

if (arg0 == launcher_py or arg0 == ''):
    if (len(sys.argv) <= 1 or 
        (len(sys.argv[1]) <= 0 or sys.argv[1].startswith('-'))):
        print_help()
        exit(1);
    arg0 = os.path.basename(sys.argv[1])

prog = arg0
logger.debug("Program name resolved: '%s'", prog)

# prepare dictionary for individual configurations
cfg_file_list = ["cfg_cahe", "system_cfg", "app_generic",
        "user_generic", "user_app_specific"]
cfg_fs = dict.fromkeys(cfg_file_list);

# file : path, mtime, config parser instance
for key in cfg_fs.keys():
    cfg_fs[key] = dict.fromkeys(["path", "mtime", "cfg"])
    cfg_fs[key]["cfg"] = dict()

# try to find corresponding config files (depth first search basicaly)
cfg_fs["system_cfg"]["path"] = get_config_path(launcher, '%s:%s' 
    % (xdg_cfg["XDG_CONFIG_DIRS"], xdg_cfg["XDG_DATA_DIRS"]))
cfg_fs["app_generic"]["path"] = get_config_path(prog, '%s:%s' 
    % (xdg_cfg["XDG_CONFIG_DIRS"], xdg_cfg["XDG_DATA_DIRS"]))
cfg_fs["user_generic"]["path"] = get_config_path(launcher, '%s:%s' 
    % (xdg_cfg["XDG_CONFIG_HOME"], xdg_cfg["XDG_DATA_HOME"]))
cfg_fs["user_app_specific"]["path"] = get_config_path(prog, '%s:%s' 
    % (xdg_cfg["XDG_CONFIG_HOME"], xdg_cfg["XDG_DATA_HOME"]))
cfg_fs["cfg_cahe"]["path"] = get_config_path(prog, xdg_cfg["XDG_CACHE_HOME"])

# verify that cache is not older than static cfg files
cache_up_to_date = True
mtime = None

for fl in cfg_file_list:
    path = cfg_fs[fl]["path"]

    if ((fl != "cfg_cahe" and mtime is None) or
            (fl == "cfg_cahe" and path is None)):
        cache_up_to_date = False
        break

    if path is None:
        continue

    cfg_fs[fl]["mtime"] = os.path.getmtime(path)

    if (fl == "cfg_cahe"):
        mtime = cfg_fs[fl]["mtime"]

    if (mtime < cfg_fs[fl]["mtime"]):
        cache_up_to_date = False
        break

# prepare efective config
if (cache_up_to_date):
    # create new instance of ini-file parser (to be safe)
    iniParser = get_ini_parser()
    iniParser.read_file(open(cfg_fs["cfg_cahe"]["path"]))

    # process and validate
    if (not process_configuration(iniParser, cfg)):
        logger.error("Cached configuration in file '%s' could not be"
            + "be processed. Removing file. Please relunch application.",
             cfg_fs["cfg_cahe"]["path"])
        os.remove(cfg_fs["cfg_cahe"]["path"])
        exit(3)

    if (not validate_cfg(cfg)):
        logger.error("Final configuration does not have all the required"
                     + " values. Please verify configuration files.")
        exit(2)
    
else:
    for fl in cfg_file_list:
        iniParser = get_ini_parser() 

        # no such config was found (should never happend), skipping ...
        if (cfg_fs[fl]["path"] is None): 
            logger.info("Config file '%s' (internal name)"
                         + " not found. Skipping file.", fl)
            continue

        # read configuration
        try:
            logger.info("Reading configuration from '%s' file at '%s'",
                    fl, cfg_fs[fl]["path"])
            iniParser.read_file(open(cfg_fs[fl]["path"]))
        except:
            logger.error("Configuration could not be parsed."
                         + " Stopping further processing.")
            break

        # proces the values
        if (not process_configuration(iniParser, cfg_fs[fl]["cfg"])):
            logger.error("Configuration in file '%s' could not be"
                    + "be processed. Skipping file.",
                    cfg_fs[fl]["path"])
            continue

       # pudb.set_trace()

        if (("stopFurtherConfigProcessing" in cfg_fs[fl]["cfg"]) and
            (cfg_fs[fl]["cfg"]["stopFurtherConfigProcessing"] == True)):
            logger.info("Config file '%s' sets flag to stop further"
                        + " processing. Only already read configuration"
                        + " will be used.", cfg_fs[fl]["path"])
            break

    # merge to final effective configuration
    for fl in cfg_file_list:
        if (cfg_fs[fl]["cfg"] is None or  len(cfg_fs[fl]["cfg"]) == 0):
            continue

        logger.debug("Config '%s': %s", fl, cfg_fs[fl]["cfg"])
        clone_ini_cfg(cfg_fs[fl]["cfg"], cfg)

        cfg = merge_configuration(cfg, cfg_fs[fl]["cfg"])

    # validate configuration 
    if (not validate_cfg(cfg)):
        logger.error("Final configuration does not have all the required"
                     + " values. Please verify configuration files.")
        exit(2)

    # if there is not already existing cache file get path to store one
    if (cfg_fs["cfg_cahe"]["path"] is None or 
            len(cfg_fs["cfg_cahe"]["path"]) == 0):
        d = os.path.join(xdg_cfg["XDG_CACHE_HOME"], prog)
        cfg_fs["cfg_cahe"]["path"] = os.path.join(d, cfg_name)

        if (not os.path.isdir(d)):
            try:
                mkdirs(d)
            except:
                cfg_fs["cfg_cahe"]["path"] = None
                logger.error("Directory '%s' used to store cached config"
                        + " file for launching application next time"
                        + " does not exist and could not be created.", d)
        
 
    # create cache file for later use (next lauch)
    if (cfg_fs["cfg_cahe"]["path"] is not None and
            cache_up_to_date == False):
        iniParser = get_ini_parser() 
        iniParser.read_dict(cfg)

        try:
            with open(cfg_fs["cfg_cahe"]["path"], 'w') as config:
                iniParser.write(config)
            logger.info("Cached config file created")

        except:
            logger.error("Could not create or write into cache config"
                    + " file '%s' used to store processed configuration.",
                    cfg_fs["cfg_cahe"]["path"])

    
# In any case configuration should be valid at this point or
# the script should have exited.

if (cfg["jvm"]["classPath"] == "dynamic"):
    logger.debug("Dynamic class path used")
    # TODO: replace exit by launching the cp generetor.
    exit(0);

# launch the application
args = [cfg["jvm"]["jvmBinary"], cfg["jvm"]["options"], ["-classpath"],
        cfg["jvm"]["classPath"], cfg["jvm"]["mainClass"],
        cfg["application"]["arguments"]
]

args = list(itertools.chain.from_iterable(args))

# filter nonexisting options and empty strings
args = list(filter(None, args))
args = list(filter(lambda x: (x is not None and x != ""), args))

print_args = list()
for arg in args:
    if (re.search(r"\s", arg)):
        arg = '"{}"'.format(arg)
    print_args.append(arg)

cmd_string = " ".join(print_args)
logger.info("Launching application: '%s'", cmd_string)

# if I dont want actualy launch application during testing
if (halt_launch == True):
    exit(0)

# actual launch of application
exit(subprocess.run(args).returncode)



# _____________________________________________________________________
