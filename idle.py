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
        self.statlevel = G.USR[userID][id + "_level"]
        self.scaling = G.IDLE[id]
        self.prices = G.IDLE.prices[id]

        def _calculate_price(self):
            """Calculate price to upgrade the stat."""
            if self.prices.function == "exponential":
                return tools.exponential(
                    self.prices.base, self.prices.mult, self.statlevel
                )
            elif self.prices.function == "linear":
                return tools.linear(
                    self.prices.base, self.prices.mult, self.statlevel
                )
            elif self.prices.function == "log":
                return tools.logar(
                    self.prices.base, self.prices.mult, self.statlevel
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
                self.statlevel + increaseLevel
            )
        elif self.scaling.function == "linear":
            return tools.linear(
                self.scaling.base, self.scaling.mult,
                self.statlevel + increaseLevel
            )
        elif self.scaling.function == "log":
            return tools.logar(
                self.scaling.base, self.scaling.mult,
                self.statlevel + increaseLevel
            )
        else:
            raise ValueError("Unsupported formula type '{}'".format(
                self.prices.function))

    def upgrade(self, value=1):
        """Award the player some level in this stat."""
        tools.update_stat(self.user, self.id + "_level", increase=value)

    def downgrade(self, value=1):
        """Reduce the player level by some value."""
        tools.update_stat(self.user, self.id + "_level", increase=-value)


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
            output.add(G.LOC.commands.harvest.overproduced.format(
                G.OPT.prefix + G.LOC.commands.upgrade.id))

        joules_produced = production_time * production.value()
        joules_produced *= G.IDLE.harvest.achievebonus ** tools.count_achieves(userID)
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
        # >> Upgrade attack help
        out.add(G.LOC.commands.upgrade.upgradable.attack.format(
            G.LOC.commands.upgrade.IDs.attack,
            round(stats.attack.value(), 2),
            round(stats.attack.value(1), 2),
            stats.attack.upgrade_price
        ).split("|"))
        return "```" + out.pretty_parse() + "```"

    elif message.args[0] in stat_names:
        try:
            times = int(message.args[1])
            if times <= 0:
                times = 1
        except (ValueError, IndexError):
            times = 1
        i = 0
        while i < times:
            stats = make_all_stats(userID)
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
                break
            i += 1
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


# Attack ------------------------------------------------------------------

class Titan():
    """Used to calculate initial values for titans"""
    def __init__(self, level):
        self.level = level
        self.hp = level ** G.IDLE.titan.level_exp * G.IDLE.titan.base_hp
        # This is a function that tends to 0 @ level -> inf
        # The smaller the armor constant the slower the armor grows.
        b = G.IDLE.titan.armor_constant
        self.armor = 1 / (b * (self.level ** 2) + 1)
        self.reward = level ** G.IDLE.titan.reward_constant / self.armor


def spawn_titan(guild):
    """Spawns a titan in the current guild."""
    if isinstance(G.GLD[guild].titan_status, bool) is False:
        # We never spawned a titan before, so we start @ titan level = 0
        G.GLD[guild].titan_level = 0
    tools.update_guild(guild_id=guild, stat="titan_status", set=True)
    tools.update_guild(guild_id=guild, stat="titan_level", increase=1)
    tools.update_guild(guild_id=guild, stat="titan_damage", set=0)
    return G.GLD[guild].titan_level


def attack_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.attack.id):
        return True
    return False


def attack_logic(message):
    user_id = str(message.author.id)
    user_guild = str(message.author.guild.id)
    # If we don't have any titans, we cannot attack.
    if G.GLD[user_guild].titan_status is not True:
        return G.LOC.commands.attack.notitan
    stats = make_all_stats(user_id)
    titan = Titan(G.GLD[user_guild].titan_level)
    args = tools.MsgParser(message.content).args
    # Attempt to get a value for joules spent
    try:
        raw_damage = int(args[0])
    except (ValueError, IndexError):
        return G.LOC.commands.attack.notrecognized
    # If the user doesn't have enough joules, they cannot attack
    if G.USR[user_id].joules < raw_damage:
        return G.LOC.commands.attack.onfailure.format(G.USR[user_id].joules)
    # Remove the joules spent:
    tools.update_stat(user_id=user_id, stat="joules", increase=-raw_damage)

    if isinstance(G.USR[user_id].attacks, list) is False:
        # User has never attacked before
        G.USR[user_id].attacks = []
    if user_guild not in G.USR[user_id].attacks:
        G.USR[user_id].attacks.append(user_guild)

    damage = raw_damage * stats.attack.value() * titan.armor
    tools.update_guild(guild_id=user_guild, stat="titan_damage", increase=damage)
    remaining_hp = titan.hp - G.GLD[user_guild].titan_damage

    if G.GLD[user_guild].titan_damage >= titan.hp:
        # The titan was killed by this attack
        tools.update_guild(guild_id=user_guild, stat="titan_status", set=False)
        for id, user in G.USR.items():
            if isinstance(user.attacks, list) is False:
                continue
            if user_guild in user.attacks:
                # Award tokens to this player.
                G.USR[id].tokens += max(round(titan.reward, 0), 1)
                G.USR[id].attacks.remove(user_guild)
        tools.save_users()
        return G.LOC.commands.attack.onkill.format(
            damage, max(round(titan.reward, 0), 1)
        )
    else:
        return G.LOC.commands.attack.onsuccess.format(
            damage, remaining_hp, round(remaining_hp / titan.hp * 100, 2)
        )
    # We should never get here
    assert False, "Attack function did not escape correctly"


def make_commands():
    tools.add_command(logic=harvest_logic, permission=harvest_perm)
    tools.add_command(logic=gamehelp_logic, permission=gamehelp_perm)
    tools.add_command(logic=upgrade_logic, permission=upgrade_perm)
    tools.add_command(logic=attack_logic, permission=attack_perm)
