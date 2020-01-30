from pathlib import Path
import tools


def initialize(options_path):
    global OPT
    global USR
    global GLOC
    global GLD
    global COMMANDS
    global ACHIEVES

    # Load options
    OPT = tools.load(options_path)

    # Initialize guild and user files if non existent
    if Path(OPT.users_path).exists() is False:
        print("Making a new users file. I was probably just installed.")
        tools.initialize_empty(OPT.users_path)
    if Path(OPT.guilds_path).exists() is False:
        print("Making a new guilds file. I was probably just installed.")
        tools.initialize_empty(OPT.guilds_path)

    # Load locale, guild and user files
    GLOC = tools.load(OPT.locale_path)
    USR = tools.load(OPT.users_path, default=None)
    GLD = tools.load(OPT.guilds_path, default=None)
    print("Options, locale and user files loaded. I remembered {0} users.".format(len(USR)))

    COMMANDS = []
    ACHIEVES = []

    return True


def updateLOC(loc):
    global LOC
    LOC = loc
    return True
