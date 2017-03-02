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
import hashlib          #hashing algorithms for dynamic class path

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

halt_launch = True

# efective configuration 
cfg = dict()

# required and optional values in configuration
cfg_requires = {
    "jvm" : ["jvmBinary"], # , "", ""
    "application" : ["classPath", "mainClass"] 
}

cfg_optionals = {
    "jvm" : ["options"], # , "", ""
    "application" : ["arguments"] 
    
}

# values that should be parsed during processing
cfg_parse = {
    "launcher" : ["stopFurtherConfigProcessing", "enableAbrt", "generator"],
    "jvm" : ["jvmBinary", "options"], # , "", ""
    "application" : ["arguments", "classPath", "mainClass"] 
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



def is_executable(path):
    return os.path.isfile(path) and os.access(path, os.X_OK)



def get_ini_parser():
    iniParser = configparser.ConfigParser(empty_lines_in_values=False)
    iniParser.optionxform = str
    return iniParser



def get_logger(name=launcher, level=None, sfx=None):
    if (sfx != None):
        name +=sfx

    logger = logging.getLogger(name)

    # logging level for whole logger
    # can chnge log level in a subsequent call
    if (level == None):
        logger.setLevel(loglvl)

    if (not logger.hasHandlers()): 
        # handler for stderr
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s]: %(message)s")
        handler.setFormatter(formatter)
        handler.setLevel(logging.ERROR) # only erros are needed
        logger.addHandler(handler)

        # handler for logging to file
        handler = logging.FileHandler(logname)
        formatter = logging.Formatter("%(asctime)s|[%(levelname)s] %(name)s: %(message)s")
        handler.setFormatter(formatter)
        # logs everithing that goes to the logger
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
        for field, value in config_parser[section].items():
            if (section == "application" and field == "classPath" and
                    value == "dynamic"):
                continue
            
            if (section in cfg_parse and field in cfg_parse[section]):
                value = parse_cfg_value(value)

            # class path has to be garanteed to be expanded
            if ((section == "application" and field == "classPath") or
                    (section == "launcher" and field == "generator")):
                for i, item in enumerate(value):
                    value[i] = os.path.expanduser(value[i])
                    value[i] = os.path.expandvars(value[i])

            cfg[section][field] = value

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
                if (isinstance(value, list)):
                    clone[key][option] = list(value)
                elif (isinstance(value, dict)):
                    clone[key][option] = dict(value)
                else:
                    clone[key][option] = value

        if (isinstance(source[key], list)):
            clone[key] = list(source[key])

        clone[key] = item

    return None



# Merges two processed configurations in a way that values form
# "what" configuration overrides values from "into" configuration.
# @param dictionary with configuration to merge into 
# @param dictionary with configuration to coppy from
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

    for key, fields in source.items():
        if (key not in target and aor == True):
            continue
        elif (key not in target):
            target[key] = None

        if (clone == True):
            # if target is not a dictionary, override
            if (not isinstance(target[key], dict) and
                     isinstance(source[key], dict)):
                target[key] = dict(source[key]);

        # if target and source are dictionaries only override
        # and add values, fields that are not in source must stay intact
        if (isinstance(target[key], dict) and 
                isinstance(source[key], dict)):
            for field, value in source[key].items():
                target[key][field] = value

        # if clone is not active 
        else :
            target[key] = fields

    if (aor == True):
        for key, fields in target.items():
            if (key not in source):
                del target[key]
                continue

            for field, value in target[key]:
                if (field not in source[key]):
                    del target[key][field]

    return target



def validate_cfg(cfg):
    logger = get_logger()
    logger.info("Validating configuration for required values.")
    cfg_valid = True

    for section, fields in cfg_requires.items():
        if ((section not in cfg) or
                (not isinstance(cfg[section], dict))):
            logger.info("Final configuration missing required"
                        + " section '%s'", section)
            cfg_valid = False
            break

        for field in fields:
            if (field not in cfg[section]):
                logger.info("Final configuration missing required"
                            + " field '%s' in section '%s'",
                            field, section)
                cfg_valid = False
                break

            # if classpath is supposed to be dynamic there are more
            # required fields 
            if (section == "application" and
                    field == "classPath" and 
                    cfg[section][field] == "dynamic"):

                new_requires = ["generator", "genInput"]
                new_optionals = ["cpHash", "genPath"]

                if ("launcher" not in cfg_requires):
                    cfg_requires["launcher"] = new_requires
                else :
                    cfg_requires["launcher"].extend(new_requires)

                if ("launcher" not in cfg_optional):
                    cfg_optionals["launcher"] = new_optionals
                else :
                    cfg_optionals["launcher"].extend(new_optionals)

            if ((section == "jvm" and field == "jvmBinary") or
                    (section == "launcher" and field == "generator")):
                if (not is_executable(cfg[section][field][0])):
                    # cfg[section][field] is a list so "[0]" is necessary
                    cfg_valid = False
                    break

    if (cfg_valid == False):
        logger.debug(cfg)

        return cfg_valid

    for section, fields in cfg_optionals.items():
        if ((section not in cfg) or
                (not isinstance(cfg[section], dict))):
            logger.debug("Filling in omitted section '%s' to"
                        + " final configuration", section)
            cfg[section] = dict()

        for field in fields:
            if (field not in cfg[section]):
                logger.info("Filling in omitted field '%s' in"
                            + " section '%s'", field, section)
                cfg[section][field] = None

    return True
   


def cache_dynamic_cp(classpath, digest, path=None):
    # check or create the path for file
    if (path is None or len(path) == 0):
        d = os.path.join(xdg_cfg["XDG_CACHE_HOME"], prog)
        path = os.path.join(d, cfg_name)

    # directory for cache file must exist
    if (not os.path.isdir(d)):
        try:
            mkdirs(d)
        except:
            logger.error("Directory '%s' used to store cached config"
                + " file for launching application next time"
                + " does not exist and could not be created.", d)
            return None

    # create dictionary of values to store in cache file
    iniParser = get_ini_parser() 
    iniParser["launcher"]["cpHash"] = digest
    iniParser["launcher"]["genPath"] = classpath

    try:
        with open(path, 'w') as config:
            iniParser.write(config)
        logger.info("Cached config file created")

    except:
        logger.error("Could not create or write into cache config"
                + " file '%s' used to store processed configuration.",
                path)


    return None
 
# Main_________________________________________________________________
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
cfg_file_list = ["system_cfg", "app_generic",
        "user_generic", "user_app_specific", "cfg_cahe"]
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

# prepare efective config
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

##    pudb.set_trace()

    if (("launcher" in cfg_fs[fl]) and
            ("stopFurtherConfigProcessing" in 
                cfg_fs[fl]["cfg"]["launcher"]) and
            (cfg_fs[fl]["cfg"]["launcher"]["stopFurtherConfigProcessing"]
                == True)):
        logger.info("Config file '%s' sets flag to stop further"
                    + " processing. Only already read configuration"
                    + " will be used.", cfg_fs[fl]["path"])
        break

# merge to final effective configuration
for fl in cfg_file_list:
    if (cfg_fs[fl]["cfg"] is None or  len(cfg_fs[fl]["cfg"]) == 0):
        continue

    logger.debug("Config '%s': %s", fl, cfg_fs[fl]["cfg"])
    cfg = merge_configuration(cfg, cfg_fs[fl]["cfg"])

# validate configuration 
if (not validate_cfg(cfg)):
    logger.error("Final configuration does not have all the required"
                 + " values. Please verify configuration files.")
    exit(2)

# In any case configuration should be valid at this point or
# the script should have exited.

# if "dynamic" classpath check the hash and replace the keyword with it
if (cfg["application"]["classPath"] == "dynamic"):
    logger.debug("Dynamic class path used")

    h = hashlib.sha256()
    h.update(cfg["launcher"]["genInput"].encode('utf-8'))
    # launcher.generator is parsed value and so it is turned
    # into form of a list
    h.update(cfg["launcher"]["generator"][0].encode('utf-8'))
    hexd = h.hexdigest()

    # compare hashes of generator inputs
    if (hexd != cfg["launcher"]["cpHash"]):
        args = list(cfg["launcher"]["generator"])
        args.extend(cfg["launcher"]["genInput"])

        # run classpath generator
        logger.info("Generating class path with use of external process.")
        logger.info(args)

        generator = sp.Popen(args, stderr=sp.PIPE, stdout=sp.PIPE)
        # stdout, stderr = process.comunicate()
        cfg["launcher"]["genPath"], stderr = generator.comunicate()
        if (generator.returncode != 0):
            logger.error("Generating dynamic class path failed. Generating"
                       + " process exited with return code %d. Exiting ...",
                       generator.returncode)
            logger.error("STDERR of generator process - dump:\n%s", stderr)
            exit(2);

        # store and cache newly generated classpath
        cache_dynamic_cp(cfg["launcher"]["genPath"], hexd)

    # get classpath usable in following code
    # already expanded classpath is expected
    cfg["jvm"]["classPath"] = shlex.split(cfg["launcher"]["genPath"])

# launch the application
args = [cfg["jvm"]["jvmBinary"], cfg["jvm"]["options"], ["-classpath"],
        cfg["application"]["classPath"], cfg["application"]["mainClass"],
        cfg["application"]["arguments"]
]

# "jvm.options" and "application.arguments" are not required and they
# are set as None if missing - Non is not itreable following line fixes
# that issue
args = list(filter(None, args))

# we have a list of lists that needs to be flatened with predefined order
args = list(itertools.chain.from_iterable(args))

# filter nonexisting options and empty strings
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
    print(cmd_string)
    exit(0)

# actual launch of application
exit(subprocess.run(args).returncode)



# _____________________________________________________________________
