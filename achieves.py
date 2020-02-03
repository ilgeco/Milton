import globals as G
import tools
from idle import Statistic


# Define achievements
class Achievement():
    def __init__(self, trigger, id):
        self.trigger = trigger
        self.id = id

    def award(self, user_id):
        """Award the achievement to the user

        Handles both setting the achieved status to true and giving the correct
        phrase to give the user upon achieving it.
        """
        G.USR[str(user_id)][self.id] = True
        tools.save_users()
        return G.LOC.msg.format_yes.format(
            G.LOC.achievements[self.id].name,
            G.LOC.achievements[self.id].condition
        )

    def check_trigger(self, message, user_id):
        if self.trigger(message) is True and \
                G.USR[str(user_id)][self.id] in [False, None]:
            return True


def add_achievement(trigger, id):
    G.ACHIEVES.append(Achievement(trigger, id))
    return True


# -------------------------------------------------------------------
def ac_use_MLA(message):
    if G.USR[str(message.author.id)].commandCount >= 1:
        return True
    return False


def ac_use_MLA2(message):
    if G.USR[str(message.author.id)].commandCount >= 50:
        return True
    return False


def ac_use_MLA3(message):
    if G.USR[str(message.author.id)].commandCount >= 100:
        return True
    return False


def ac_use_MLA4(message):
    if G.USR[str(message.author.id)].commandCount >= 1000:
        return True
    return False


def ac_got_lucky(message):
    if G.USR[str(message.author.id)].gotLucky:
        return True
    return False


def ac_got_unlucky(message):
    if G.USR[str(message.author.id)].gotUnlucky:
        return True
    return False


def ac_many_facts(message):
    if G.USR[str(message.author.id)].factCount >= 30:
        return True
    return False


def ac_joules1(message):
    if G.USR[str(message.author.id)].joules >= 100:
        return True
    return False


def ac_joules2(message):
    if G.USR[str(message.author.id)].joules >= 17_000:
        return True
    return False


def ac_joules3(message):
    if G.USR[str(message.author.id)].joules >= 1_000_000:
        return True
    return False


def ac_joules_blazeit(message):
    if G.USR[str(message.author.id)].joules >= 4_206_969:
        return True
    return False


def ac_joules_sixtynine(message):
    if str(round(G.USR[str(message.author.id)].joules, 0)).startswith == 69:
        return True
    return False


def ac_production1(message):
    userID = str(message.author.id)
    stat = Statistic("production", userID)
    if stat.value() * 60 >= 5:
        return True
    return False


def ac_production2(message):
    userID = str(message.author.id)
    stat = Statistic("production", userID)
    if stat.value() * 60 >= 100:
        return True
    return False


def ac_production_sun(message):
    userID = str(message.author.id)
    stat = Statistic("production", userID)
    if stat.value() >= 3.84e26:
        return True
    return False


def ac_production3(message):
    userID = str(message.author.id)
    stat = Statistic("production", userID)
    if stat.value() * 60 >= 500:
        return True
    return False


def ac_production_eleveneleven(message):
    userID = str(message.author.id)
    stat = Statistic("production", userID)
    if stat.value() * 60 >= 1111:
        return True
    return False


def make_achievements():
    add_achievement(ac_use_MLA, "use_MLA")
    add_achievement(ac_use_MLA2, "use_MLA2")
    add_achievement(ac_use_MLA3, "use_MLA3")
    add_achievement(ac_use_MLA4, "use_MLA4")
    add_achievement(ac_got_lucky, "critical_win")
    add_achievement(ac_got_unlucky, "critical_failure")
    add_achievement(ac_many_facts, "many_facts")
    add_achievement(ac_joules1, "joules1")
    add_achievement(ac_joules2, "joules2")
    add_achievement(ac_joules3, "joules3")
    add_achievement(ac_joules_blazeit, "joules_blazeit")
    add_achievement(ac_joules_sixtynine, "joules_sixtynine")
    add_achievement(ac_production1, "production1")
    add_achievement(ac_production2, "production2")
    add_achievement(ac_production3, "production3")
    add_achievement(ac_production_sun, "production_sun")
    add_achievement(ac_production_eleveneleven, "production_eleveneleven")

    return True
