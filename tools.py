import math
import random
import json
from pathlib import Path
import munch
from itertools import zip_longest
import globals as G
from mpmath import *


def get_random_line(file: str) -> str:
    """Returns a random line in a file.

    Args:
        file: str
            Path to target file

    Returns: str
        Random line from the target file.
    """
    path = Path(file)
    with path.open("r") as file:
        items = [a for a in file if a != ""]
    return random.choice(items)


def save(file: Path, dictionary: dict) -> True:
    """Write target dirty to JSON file.

    Doesn't sort keys as it often breaks.

    Args:
        file: str
            Path to target file
        dictionary: dirty
            Dictionary to write to file
    Returns:
        True
    """
    def pre_process(dirty: dict) -> dict:
        for key, item in dirty.items():
            if isinstance(item, dict):
                dirty[key] = pre_process(item)
            if isinstance(item, mpf):
                dirty[key] = nstr(item, 16)
        return dirty

    file = Path(file)
    with file.open("w+") as file:
        # Don't make this sort keys as it breaks, for some reason
        json.dump(obj=pre_process(dictionary), fp=file, indent=2)
    return True


def load(file, default: bool = False):
    """Load target json dict from file, and munch-ify it.

    Args:
        file: str
            Path to target file to load
        default: False or any
            If false, dictionary doesn't have a default. Otherwise, the dictionary has this value
            as default

    Returns:
        Munch dictionary
    """
    file = Path(file)
    with file.open("r") as file:
        if default is False:
            return munch.munchify(json.load(file))
        else:
            return munch.DefaultMunch.fromDict(json.load(file), default)


def save_users():
    """Save user dictionary to default user.json path"""
    save(file=G.OPT.users_path, dictionary=G.USR)
    return G.reload_users()


def save_guilds():
    """Save guild dictionary to default guilds.json path"""
    return save(file=G.OPT.guilds_path, dictionary=G.GLD)


def initialize_empty(path: str, content="{}") -> True:
    """Create empty .json file to target path."""
    with Path(path).open("w+") as f:
        f.write(content)
    return True


def update_user(user_id, stat, increase=None, set=None) -> True:
    """Update a value in the user file, then save users"""
    # TODO: This shadows "set()" - change?
    # Simple logic checks
    if increase is None and set is None:
        raise ValueError("Must specify either increase or set.")
    if increase is not None and set is not None:
        raise ValueError("Cannot increase and set at the same time.")
    # Set or increase variable:
    if increase is not None:
        if isinstance(G.USR[str(user_id)][stat], str):
            G.USR[str(user_id)][stat] = mpf(G.USR[str(user_id)][stat])
        G.USR[str(user_id)][stat] += increase
    elif set is not None:
        G.USR[str(user_id)][stat] = set
    save_users()
    return True


def update_guild(guild_id, stat, increase=None, set=None) -> True:
    """Update a value in the guild file, then save users"""
    # Simple logic checks
    if increase is None and set is None:
        raise ValueError("Must specify either increase or set.")
    if increase is not None and set is not None:
        raise ValueError("Cannot increase and set at the same time.")
    # Set or increase variable:
    if increase is not None:
        if isinstance(G.GLD[str(guild_id)][stat], str):
            G.GLD[str(guild_id)][stat] = mpf(G.GLD[str(guild_id)][stat])
        G.GLD[str(guild_id)][stat] += increase
    elif set is not None:
        G.GLD[str(guild_id)][stat] = set
    save_guilds()
    return True


def exponential(base, multiplier, level):
    """Simple exponential formula"""
    return fmul(base, power(multiplier, level))


def linear(base, multiplier, level):
    """Simple linear formula"""
    return base + fmul(multiplier, level)


def logarithm(base, multiplier, level):
    """Simple log formula"""
    return base * log(level + multiplier, multiplier)


def linear_multiplier(base, multiplier, level, level_multiplier, level_threshold):
    """Linear scaling with bonus multiplier at X levels"""
    base_value = base + multiplier * level
    multiplier_times = (level // level_threshold)
    return base_value * (level_multiplier ** multiplier_times)


def add_command(logic, permission, where="channel", epoch=0):
    """Adds command to global command list"""
    G.COMMANDS.append(Command(logic, permission, where, epoch))


def break_message(message, length=2000):
    """Breaks a long message into substrings.

    The default value is @ 2000 characters, as discord can only send 2k-long messages.
    """
    # TODO: This is full of errors but works. Maybe there's a better way to do this?
    strings = []

    def _split_message(message, length=2000):
        global strings
        if len(message) > length:
            strings.append(message[length:])
            _split_message(message[length:], length)
        else:
            strings.append(message)
            return True

    return strings


def count_achieves(user_id: str) -> int:
    """Count the number of achievements unlocked by this user."""
    i = 0
    for achieve in G.LOC.achievements.keys():
        if G.USR[user_id][achieve] is True:
            i += 1
    return i


def fn(number: float,
       threshold: int = 100_000,
       decimals: int = 2) -> str:
    """Short for 'format number'.

    Takes a number and formats it into human-readable form.
    If it's larger than threshold, formats it into a more compact form.

    Args:
        number: float or int
            Number to format
        threshold: int
            Threshold under which not to format. Defaults at 100_000
        decimals: int
            Number of decimal places to give to the number before formatting.

    Returns:
        String with formatted number.
    """
    number = mpf(number)
    if number < threshold:
        return str(round(float(number), decimals))
    return nstr(number, decimals)


class MsgBuilder:
    """Class to build messages to push to chat.

    Parses lists containing messages to send to chat. It contains them inside a list of lists.
    """
    def __init__(self):
        # When adding to msg, remember to only add lists of one or more strings
        self.msg = []

    def add(self, line: str):
        """Add a new line to be parsed."""
        if isinstance(line, str):
            line = [line]
        self.msg.append(line)

    def append(self, line, sep=""):
        """Appends line to the end of last string in the message.

        Args:
            line: str
                String to append.
            sep: str
                Separator between string and string to be appended.
        """
        if not self.msg:
            self.add(line)
        else:
            self.msg[-1][-1] += (sep + line)

    def prepend(self, line, sep=""):
        """Prepends line to the start of last string in the message.

        Args:
            line: str
                String to append.
            sep: str
                Separator between string and string to be prepended.
        """
        if not self.msg:
            self.add(line)
        else:
            self.msg[-1][-1] = line + sep + self.msg[-1][-1]

    def parse(self):
        """Parses itself as a list of the fewest number of strings possible.

        Doesn't exceed 2000 characters while creating strings to push to chat.
        """
        messages = []
        formatted = ""
        for row in self.msg:
            if len(formatted + " ".join(row)) <= 2000:
                formatted += " ".join(row) + "\n"
            else:
                messages.append(formatted.rstrip())
                formatted = " ".join(row) + "\n"
        messages.append(formatted.rstrip())
        return messages

    def pretty_parse(self, padding=2):
        """Pretty parse the list of words as columns.

        Handles giving each string the correct number of spaces, plus adds the back-ticks
        to mark this message as code.

        Args:
            padding: int
                Spaces to add in addition to those to make columns equal.
                Defaults to 2
        """
        # TODO: This doesn't check for the 2k character limit.
        col_widths = [max(map(len, col)) for col in zip_longest(*self.msg, fillvalue="")]
        formatted = ""
        for row in self.msg:
            formatted += ("" + padding * " ").join(
                (val.ljust(width) for val, width in zip(row, col_widths))
            )
            formatted += "\n"
        return ["```" + formatted.rstrip() + "```"]


class MsgParser:
    """Small utility to parse messages and grab arguments separated by spaces."""
    def __init__(self, message):
        message = message.split()  # This splits @ one or more whitespaces
        self.command = message[0]
        self.args = message[1:]


class Command:
    def __init__(self, logic, permission=True, where="channel", epoch=0):
        """Class to package all command logic and permissions inside.

        Args:
            logic: fun
                Logic of the command. We expect it to return a string to push to chat.
            permission: fun or bool
                Permission function to check if logic should trigger. If set to True,
                command triggers at each message.
            where: str
            Either "channel" or "user". Where to send the message, the channel where the command
            was invoked, or directly to the user who sent it.
            Not used directly by this class.
        """
        assert where in ["channel", "user"]
        self.logic = logic
        self.permission = permission
        self.where = where
        self.epoch = epoch
