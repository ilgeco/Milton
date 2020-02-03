import globals as G
import tools
import munch
import time

# Aviable statistics:
# >> production (mult of time to award joules)
# >> maxTicks (max allowed seconds of production)


class Statistic:
    def __init__(self, id, userID):
        self.id = id
        self.name = G.LOC.commands.upgrade.IDs[id]
        self.user = userID
        # The name of the stat is normalized as "stat_level"
        self.userlevel = G.USR[userID + "_level"]
        self.scaling = G.IDLE[id]
        self.prices = G.IDLE.prices[id]

        def _calculate_price(self):
            """Calculate price to upgrade the stat."""
            if self.prices.function == "exponential":
                return tools.exponential(
                    self.prices.base, self.prices.mult, self.userlevel
                )
            elif self.prices.function == "linear":
                return tools.linear(
                    self.prices.base, self.prices.mult, self.userlevel
                )
            elif self.prices.function == "log":
                return tools.logar(
                    self.prices.base, self.prices.mult, self.userlevel
                )
            else:
                raise ValueError("Unsupported formula type '{}'".format(
                    self.prices.function))

        self.upgrade_price = _calculate_price(self)

    def value(self, increaseLevel=0):
        """Calculate the value of the statistic.

        increaselevel: int
            Increase the player level for the purpose of the calculation.
        """
        if self.scaling.function == "exponential":
            return tools.exponential(
                self.scaling.base, self.scaling.mult,
                self.userlevel + increaseLevel
            )
        elif self.scaling.function == "linear":
            return tools.linear(
                self.scaling.base, self.scaling.mult,
                self.userlevel + increaseLevel
            )
        elif self.scaling.function == "log":
            return tools.logar(
                self.scaling.base, self.scaling.mult, self.userlevel
                + increaseLevel
            )
        else:
            raise ValueError("Unsupported formula type '{}'".format(
                self.prices.function))

    def upgrade(self, value=1):
        """Award the player some level in this stat."""
        tools.update_stat(self.user, self.id + "_level", increase=value)
        tools.save_users()
        G.USR[self.user + "_level"] += value

    def downgrade(self, value=1):
        """Reduce the player level by some value."""
        tools.update_stat(self.user, self.id + "_level", increase=-value)
        tools.save_users()
        G.USR[self.user + "_level"] -= value


# Game Help ------------------------------------------------------------------
def gamehelp_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.gameHelp.id):
        return True
    return False


def gamehelp_logic(message):
    helpmsg = G.LOC.msg.gameHelp + "\n"
    for command in G.LOC.commands.values():
        if command.showHelp is True and "idle" in command.category:
            helpmsg += (
                "**" + G.OPT.prefix + command.id + "**:\n\t" + command.help + "\n"
            )
    return helpmsg


# Harvest --------------------------------------------------------------------
def harvest_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.harvest.id):
        return True
    return False


def harvest_logic(message):
    """Handles all idle game updates based on time and returns appropriate
    message to push to chat.

    For now, calculates Joules to add.
    """
    # Simplify my life - partial variable unpacking
    userID = str(message.author.id)
    output = tools.MsgBuilder()

    current_time = time.time()
    last_time = G.USR[userID].last_harvest
    tools.update_stat(user_id=userID, stat="last_harvest", set=current_time)

    # Leave this as clutter free as possible for eventual additional uses
    # >> Produce Joules
    output.add(produceJoules(userID, current_time, last_time))

    tools.save_users()
    return output.parse()


def produceJoules(userID, current_time, last_time):
    """Handles calculating joules to add as well generating the message."""
    output = tools.MsgBuilder()
    production = Statistic("production", userID)
    maxTicks = Statistic("maxTicks", userID)

    if last_time == 0:
        # I give a gift of some joules for the uninitialized user.
        tools.update_stat(user_id=userID, stat="joules", set=G.IDLE.harvest.gift)
        return G.LOC.commands.harvest.firstTime.format(
            G.IDLE.harvest.gift, round((G.IDLE.production.base * 60), 0))
    else:
        production_time = current_time - last_time
        if production_time > maxTicks.value():
            production_time = maxTicks.value()
            output.add(G.LOC.harvest.overproduced.format(
                G.OPT.prefix + G.LOC.commands.upgrade.id))

        joules_produced = production_time * production.value()
        tools.update_stat(user_id=userID, stat="joules", increase=joules_produced)
        tools.save_users()
        output.add(G.LOC.commands.harvest.production.format(
            joules_produced, G.USR[userID].joules))
        return output.parse()


# End of Harvest -------------------------------------------------------------


def upgrade_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.upgrade.id):
        return True
    return False


def upgrade_logic(message):
    userID = str(message.author.id)
    if len(message.content.split(" ")) == 1:
        return G.LOC.commands.upgrade.notrecognized.format(
            ", ".join(G.LOC.commands.upgrade.IDs.values()).rstrip(', '))
    message = tools.MsgParser(message.content)
    out = tools.MsgBuilder()
    stats = make_all_stats(userID)
    stat_names = [stat.name for stat in stats.values()]

    if message.args[0] == G.LOC.commands.upgrade.IDs.info:
        # Send information message
        out.add(G.LOC.commands.upgrade.info)
        # >> Upgrade max ticks help
        out.add(G.LOC.commands.upgrade.upgradable.maxTicks.format(
            G.LOC.commands.upgrade.IDs.maxTicks,
            round(stats.maxTicks.value() / 3600, 2),
            round(stats.maxTicks.value(1) / 3600, 2),
            stats.maxTicks.upgrade_price
        ).split("|"))
        # >> Upgrade production help
        out.add(G.LOC.commands.upgrade.upgradable.production.format(
            G.LOC.commands.upgrade.IDs.production,
            round(stats.production.value() * 60, 2),
            round(stats.production.value(1) * 60, 2),
            stats.production.upgrade_price
        ).split("|"))
        return "```" + out.pretty_parse() + "```"

    elif message.args[0] in stat_names:
        stat = [x for x in stats.values() if x.name == message.args[0]][0]
        if G.USR[userID].joules >= stat.upgrade_price:
            stat.upgrade()
            out.add(G.LOC.commands.upgrade.onsuccess.format(
                stat.upgrade_price,
                stat.name
            ))
            G.USR[userID].joules -= stat.upgrade_price
            tools.save_users()
        else:
            out.add(G.LOC.commands.upgrade.onfailure.format(
                G.USR[userID].joules,
                stat.name,
                stat.upgrade_price
            ))
        return out.parse()

    else:
        out.add(G.LOC.commands.upgrade.notrecognized.format(
            ", ".join(G.LOC.commands.upgrade.IDs.values()).rstrip(', '))
        )
        return out.parse()


def make_all_stats(userID):
    stats = munch.Munch()
    for stat in G.IDLE.prices:
        stats[stat] = Statistic(stat, userID)
    return stats


def make_commands():
    tools.add_command(logic=harvest_logic, permission=harvest_perm)
    tools.add_command(logic=gamehelp_logic, permission=gamehelp_perm)
    tools.add_command(logic=upgrade_logic, permission=upgrade_perm)
