import globals as G
import tools


class Achievement():
    def __init__(self, trigger, id):
        self.trigger = trigger
        self.id = id

    def award(self, user_id):
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
# Use a single command.
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


def make_achievements():
    add_achievement(ac_use_MLA, "use_MLA")
    add_achievement(ac_use_MLA2, "use_MLA2")
    add_achievement(ac_use_MLA3, "use_MLA3")
    add_achievement(ac_use_MLA4, "use_MLA4")
    add_achievement(ac_got_lucky, "critical_win")
    add_achievement(ac_got_unlucky, "critical_failure")
    add_achievement(ac_many_facts, "many_facts")

    return True
