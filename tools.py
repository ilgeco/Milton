import random
import json
from pathlib import Path
import munch
from itertools import zip_longest
from math import log
import globals as G


def get_random_line(file: str) -> str:
    """Returns a random line in a file."""
    path = Path(file)
    with path.open("r") as file:
        items = [a for a in file if a != ""]
    return random.choice(items)


def save(file: Path, dict):
    """Write target json dict to file"""
    file = Path(file)
    with file.open("w+") as file:
        json.dump(obj=dict, fp=file, indent=2)
    return True


def load(file, default=False):
    """Load target json dict from file, and munchify it"""
    file = Path(file)
    with file.open("r") as file:
        if default is False:
            return munch.munchify(json.load(file))
        else:
            return munch.DefaultMunch.fromDict(json.load(file), default)


def save_users():
    """Save users to default user.json path"""
    return save(file=G.OPT.users_path, dict=G.USR)


def save_guilds():
    """Save users to default user.json path"""
    return save(file=G.OPT.guilds_path, dict=G.GLD)


def initialize_empty(path, content="{}"):
    """Create empty .json file to target path."""
    with Path(path).open("w+") as f:
        f.write(content)
    return True


def update_stat(user_id, stat, increase=None, set=None):
    """Update a single stat in the user file, then save users"""
    # Simple logic checks
    if increase is None and set is None:
        raise ValueError("Must specify either increase or set.")
    if increase is not None and set is not None:
        raise ValueError("Cannot increase and set at the same time.")
    # Set or increase variable:
    if increase is not None:
        G.USR[str(user_id)][stat] += increase
    elif set is not None:
        G.USR[str(user_id)][stat] = set
    save_users()
    return True


def update_guild(guild_id, stat, increase=None, set=None):
    """Update a single stat in the user file, then save users"""
    # Simple logic checks
    if increase is None and set is None:
        raise ValueError("Must specify either increase or set.")
    if increase is not None and set is not None:
        raise ValueError("Cannot increase and set at the same time.")
    # Set or increase variable:
    if increase is not None:
        G.GLD[str(guild_id)][stat] += increase
    elif set is not None:
        G.GLD[str(guild_id)][stat] = set
    save_guilds()
    return True


def exponential(base, mult, level):
    """Simple exponential formula"""
    return base * (mult ** level)


def linear(base, mult, level):
    """Simple linear formula"""
    return base * mult * (level + 1)


def logar(base, mult, level):
    """Simple log formula"""
    return base * log(level + mult, mult)


def add_command(logic, permission):
    G.COMMANDS.append(Command(logic, permission))


def count_achieves(userID):
    i = 0
    for achieve in G.LOC.achievements.keys():
        if G.USR[userID][achieve] is True:
            i += 1
    return i


class MsgBuilder:
    # Very very simple utility to make messages with newlines.
    def __init__(self):
        self.msg = []

    def add(self, line):
        if isinstance(line, str):
            line = [line]
        self.msg.append(line)

    def append(self, line):
        if self.msg == []:
            self.msg = [line]
        else:
            self.msg[-1][-1] += line

    def parse(self):
        formatted = ""
        for row in self.msg:
            formatted += " ".join(row)
            formatted += "\n"
        return formatted[:-1]  # I do this to remove the trailing newline.

    def pretty_parse(self, padding=2):
        """If we append lists of words, pretty parses them as columns."""
        col_widths = [max(map(len, col)) for col in zip_longest(*self.msg, fillvalue="")]
        formatted = ""
        for row in self.msg:
            formatted += ("" + padding * " ").join(
                (val.ljust(width) for val, width in zip(row, col_widths))
            )
            formatted += "\n"
        return formatted[:-1]  # I do this to remove the trailing newline.


class MsgParser:
    def __init__(self, message):
        message = message.split()  # This splits @ one or more whitespaces
        self.command = message[0]
        self.args = message[1:]


class Command:
    def __init__(self, logic, permission=True, where="channel"):
        # logic is the logic of the command
        # Permission is the checks necessary to see if the command triggers
        # To the command. If not specified, defaults to true (always triggers).
        # Where is where to send the message, either to the user or the channel
        assert where in ["channel", "user"]
        self.logic = logic
        self.permission = permission
        self.where = where
