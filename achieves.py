"""Contains all functions to check for achievements"""

import globals as G
import tools
from idle import Statistic


# Define achievements
class Achievement:
    """Class that represents an achievement

    Args:
        trigger: fun
            Function that checks if the achievement is to be awarded.
        identifier : str
            Achievement ID present in locale to retrieve strings.
        status: str
            Either "current" or "legacy", affects how the achievement is counted in the help messages.
            Legacy achievements are not included in any way except if unlocked.
    """
    def __init__(self, trigger, identifier, status="current"):
        self.trigger = trigger
        self.id = identifier
        self.status = status

    def award(self, user_id):
        """Award the achievement to the user

        Handles both setting the achieved status to true and giving the correct
        phrase to give the user upon achieving it.

        Args:
            user_id: str
                User to award achievement to.

        Returns:
            String containing response to push to chat.
        """
        G.USR[str(user_id)][self.id] = True
        tools.save_users()
        return G.LOC.msg.format_yes.format(
            G.LOC.achievements[self.id].name,
            G.LOC.achievements[self.id].condition
        )

    def check_trigger(self, user_id):
        """Checks if achievement has to be given.

        Args:
            user_id: str
                User to check if achievement has to be given.
        """
        if self.trigger(str(user_id)) is True and \
                G.USR[str(user_id)][self.id] is not True:
            return True


def add_achievement(trigger, identifier, status="current"):
    """Adds achievement to global achievement list"""
    G.ACHIEVES.append(Achievement(trigger, identifier, status))
    return True


def make_achievements():
    """Adds all achievements to global achievement list"""
    # Number of commands -----------------------------------------------------
    add_achievement(
        lambda user: True if G.USR[user].commandCount >= 1 else False,
        "use_MLA")
    add_achievement(
        lambda user: True if G.USR[user].commandCount >= 50 else False,
        "use_MLA2")
    add_achievement(
        lambda user: True if G.USR[user].commandCount >= 100 else False,
        "use_MLA3")
    add_achievement(
        lambda user: True if G.USR[user].commandCount >= 1_000 else False,
        "use_MLA4")

    # Number of Joules -----------------------------------------------------
    add_achievement(
        lambda user: True if G.USR[user].joules >= 100 else False,
        "joules1")
    add_achievement(
        lambda user: True if G.USR[user].joules >= 17_000 else False,
        "joules2")
    add_achievement(
        lambda user: True if G.USR[user].joules >= 1_000_000 else False,
        "joules3")
    add_achievement(
        lambda user: True if G.USR[user].joules >= 4_206_969 else False,
        "joules_blazeit")
    add_achievement(
        lambda user: True if str(round(G.USR[user].joules, 0)).startswith("69") else False,
        "joules_sixtynine")

    # Production stats -----------------------------------------------------
    add_achievement(
        lambda user: True if Statistic("production", user).value() * 60 >= 5 else False,
        "production1")
    add_achievement(
        lambda user: True if Statistic("production", user).value() * 60 >= 100 else False,
        "production2")
    add_achievement(
        lambda user: True if Statistic("production", user).value() * 60 >= 500 else False,
        "production3")
    add_achievement(
        lambda user: True if Statistic("production", user).value() >= 3.84e26 else False,
        "production_sun")
    add_achievement(
        lambda user: True if Statistic("production", user).value() * 60 >= 1111 else False,
        "production_eleveneleven")

    # Attack stats -----------------------------------------------------
    add_achievement(
        lambda user: True if Statistic("attack", user).value() >= 300 else False,
        "attack1")
    add_achievement(
        lambda user: True if Statistic("attack", user).value() >= 10000 else False,
        "attack2")
    add_achievement(
        lambda user: True if Statistic("attack", user).value() >= 123456 else False,
        "attack3")

    # Time stat -----------------------------------------------------
    add_achievement(
        lambda user: True if Statistic("maxTicks", user).value() / 3600 >= 8 else False,
        "maxTicks1")
    add_achievement(
        lambda user: True if Statistic("maxTicks", user).value() / 3600 >= 24 else False,
        "maxTicks2")
    add_achievement(
        lambda user: True if Statistic("maxTicks", user).value() / 3600 >= (24 * 7) else False,
        "maxTicks3")

    # Titan Damage -----------------------------------------------------
    add_achievement(
        lambda user: True if G.USR[user].titan_damage >= 1e5 else False,
        "damage1")
    add_achievement(
        lambda user: True if G.USR[user].titan_damage >= 1e6 else False,
        "damage2")
    add_achievement(
        lambda user: True if G.USR[user].titan_damage >= 1e9 else False,
        "damage3")
    add_achievement(
        lambda user: True if G.USR[user].onedamage is True else False,
        "onedamage")
    add_achievement(
        lambda user: True if G.USR[user].maximum_damage >= 6_666 else False,
        "damagerecord1", status="legacy")
    add_achievement(
        lambda user: True if G.USR[user].maximum_damage >= 666_666 else False,
        "damagerecord2", status="legacy")
    add_achievement(
        lambda user: True if G.USR[user].maximum_damage >= 6_666_666 else False,
        "damagerecord3", status="legacy")
    add_achievement(
        lambda user: True if G.USR[user].instantkill is True else False,
        "instantkill")

    # Times attacked ---------------------------------------------------------------------------

    add_achievement(
        lambda user: True if G.USR[user].times_attacked >= 1 else False,
        "times_attacked1"
    )
    add_achievement(
        lambda user: True if G.USR[user].times_attacked >= 10 else False,
        "times_attacked2"
    )
    add_achievement(
        lambda user: True if G.USR[user].times_attacked >= 365 else False,
        "times_attacked3"
    )

    # Tokens -----------------------------------------------------
    add_achievement(
        lambda user: True if G.USR[user].tokens >= 1 else False,
        "tokens1")
    add_achievement(
        lambda user: True if G.USR[user].tokens >= 100 else False,
        "tokens2")
    add_achievement(
        lambda user: True if G.USR[user].tokens >= 1e6 else False,
        "tokens3")

    # Other -----------------------------------------------------
    add_achievement(
        lambda user: True if G.USR[user].gotLucky else False,
        "critical_win")
    add_achievement(
        lambda user: True if G.USR[user].gotUnlucky else False,
        "critical_failure")
    add_achievement(
        lambda user: True if G.USR[user].factCount >= 20 else False,
        "many_facts")

    return True
