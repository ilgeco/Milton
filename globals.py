"""UNSAFE FOR IMPORT
Contains all global memory dictionaries. Has to be initialized through initialize()
"""

from pathlib import Path
import tools


def initialize(options_path: str) -> True:
    """Initialize all global variables for usage in different modules.

    Uses Munch() to give java-style access to dicts. Initializes empty files if none are found.

    Vars:
        options_path: str
        String path that points to options json file.

    Returns:
        True
    """
    global OPT
    global USR
    global GLOC
    global GLD
    global COMMANDS
    global ACHIEVES
    global IDLE

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
    USR = tools.load(OPT.users_path, default=0)
    GLD = tools.load(OPT.guilds_path, default=0)
    IDLE = tools.load(OPT.idle_path)
    print("Options, locale and user files loaded. I remembered {0} users.".format(len(USR)))

    COMMANDS = []
    ACHIEVES = []

    return True


def reload_users() -> True:
    """Forces dictionary reload for users from file.

    Returns:
        True
    """
    global USR
    USR = tools.load(OPT.users_path, default=0)
    return True


def update_loc(locale: str) -> True:
    """Updates locale dictionary used by Milton to some language.

    Args:
        locale: str
        The locale to be used. Must be a valid key in locales.json
    """
    global LOC
    global GLOC
    assert locale in GLOC.keys()
    LOC = GLOC[locale]
    return True
