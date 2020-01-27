import random
import json
from pathlib import Path
import munch


def get_random_line(file: str) -> str:
    "Returns a random line in a file."
    path = Path(file)
    with path.open("r") as file:
        items = [a for a in file if a != ""]
    return random.choice(items)


def save(file: Path, dict):
    file = Path(file)
    with file.open("w+") as file:
        json.dump(obj=dict, fp=file, indent=2)
    return True


def load(file, default=False):
    file = Path(file)
    with file.open("r") as file:
        if default is False:
            return munch.munchify(json.load(file))
        else:
            return munch.DefaultMunch.fromDict(json.load(file), default)


def save_users(opt, usr):
    return save(file=opt.users_path, dict=usr)


class MsgBuilder:
    def __init__(self):
        self.msg = ""

    def add(self, line):
        if self.msg == "":
            self.msg += line
        else:
            self.msg += ("\n" + line)

    def append(self, line):
        self.msg += line
