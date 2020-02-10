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
        self.tokens = G.USR[userID].tokens

        self.token_mult = 1 / (G.IDLE.token_power * self.tokens ** 2 + 1)

        def _calculate_price(self, increaseLevel=0):
            """Calculate price to upgrade the stat."""
            if self.prices.function == "exponential":
                return tools.exponential(
                    self.prices.base,
                    self.prices.mult,
                    max(self.statlevel + increaseLevel, 0)
                )
            elif self.prices.function == "linear":
                return tools.linear(
                    self.prices.base,
                    self.prices.mult,
                    max(self.statlevel + increaseLevel, 0)
                )
            elif self.prices.function == "log":
                return tools.logar(
                    self.prices.base,
                    self.prices.mult,
                    max(self.statlevel + increaseLevel, 0)
                )
            else:
                raise ValueError("Unsupported formula type '{}'".format(
                    self.prices.function))

        self.upgrade_price = _calculate_price(self)
        self._price_fun = _calculate_price

    def recalculate_price(self, increaselevel=0):
        return self._price_fun(self, increaselevel)

    def value(self, increaseLevel=0):
        """Calculate the value of the statistic.

        increaselevel: int
            Increase the player level for the purpose of the calculation.
        """
        if self.scaling.function == "exponential":
            return tools.exponential(
                self.scaling.base,
                self.scaling.mult / self.token_mult,
                max(self.statlevel + increaseLevel, 0)
            )
        elif self.scaling.function == "linear":
            return tools.linear(
                self.scaling.base,
                self.scaling.mult / self.token_mult,
                max(self.statlevel + increaseLevel, 0)
            )
        elif self.scaling.function == "log":
            return tools.logar(
                self.scaling.base,
                self.scaling.mult ** self.token_mult,
                max(self.statlevel + increaseLevel, 0)
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

    def reset(self):
        """Reset this stat to level 0"""
        tools.update_stat(self.user, self.id + "_level", set=0)


# Game Help ------------------------------------------------------------------
def gamehelp_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.gameHelp.id):
        return True
    return False


def gamehelp_logic(message):
    out = tools.MsgBuilder()
    out.add(G.LOC.msg.gameHelp)
    for command in G.LOC.commands.values():
        if command.showHelp is True and "idle" in command.category:
            out.add(
                "**" + G.OPT.prefix + command.id + "**:\n\t" + command.help
            )
    return out.parse()


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
        tools.update_stat(user_id=userID, stat="lifetime_joules", increase=joules_produced)
        tools.save_users()
        output.add(G.LOC.commands.harvest.production.format(
            tools.fn(joules_produced),
            tools.fn(G.USR[userID].joules)
        ))
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
    current_joules = G.USR[userID].joules

    if message.args[0] == G.LOC.commands.upgrade.IDs.info:
        # Send information message
        out.add(G.LOC.commands.upgrade.info)
        # >> Upgrade max ticks help
        out.prepend("```")
        out.add(G.LOC.commands.upgrade.upgradable.maxTicks.format(
            G.LOC.commands.upgrade.IDs.maxTicks,
            round(stats.maxTicks.value() / 3600, 2),
            round(stats.maxTicks.value(1) / 3600, 2),
            tools.fn(stats.maxTicks.upgrade_price)
        ).split("|"))
        if stats.maxTicks.upgrade_price <= current_joules:
            out.append(" < OK!")
        # >> Upgrade production help
        out.add(G.LOC.commands.upgrade.upgradable.production.format(
            G.LOC.commands.upgrade.IDs.production,
            round(stats.production.value() * 60, 2),
            round(stats.production.value(1) * 60, 2),
            tools.fn(stats.production.upgrade_price)
        ).split("|"))
        if stats.production.upgrade_price <= current_joules:
            out.append(" < OK!")
        # >> Upgrade attack help
        out.add(G.LOC.commands.upgrade.upgradable.attack.format(
            G.LOC.commands.upgrade.IDs.attack,
            round(stats.attack.value(), 2),
            round(stats.attack.value(1), 2),
            tools.fn(stats.attack.upgrade_price)
        ).split("|"))
        if stats.attack.upgrade_price <= current_joules:
            out.append(" < OK!")
        out.append("```")
        return out.pretty_parse()

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
                    tools.fn(stat.upgrade_price),
                    stat.name
                ))
                G.USR[userID].joules -= stat.upgrade_price
                tools.save_users()
            else:
                out.add(G.LOC.commands.upgrade.onfailure.format(
                    tools.fn(G.USR[userID].joules),
                    stat.name,
                    tools.fn(stat.upgrade_price)
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
    out = tools.MsgBuilder()

    # If we don't have any titans, we cannot attack.
    if G.GLD[user_guild].titan_status is not True:
        return G.LOC.commands.attack.notitan
    stats = make_all_stats(user_id)
    titan = Titan(G.GLD[user_guild].titan_level)
    args = tools.MsgParser(message.content).args

    # Attempt to get a value for joules spent
    try:
        raw_damage = float(args[0])
    except (ValueError, IndexError):
        out.add(G.LOC.commands.attack.notrecognized)
        return out.parse()

    if raw_damage <= 0:
        out.add(G.LOC.commands.attack.zerofailure)
        return out.parse()

    if G.USR[user_id].joules < raw_damage:
        out.add(G.LOC.commands.attack.onfailure.format(
            tools.fn(G.USR[user_id].joules)
        ))
        return out.parse()

    tools.update_stat(user_id=user_id, stat="joules", increase=-raw_damage)

    # Check for achievement
    if int(raw_damage) == 1:
        tools.update_stat(user_id=user_id, stat="onedamage", set=True)

    if isinstance(G.USR[user_id].attacks, list) is False:
        # User has never attacked before
        G.USR[user_id].attacks = []
    if user_guild not in G.USR[user_id].attacks:
        G.USR[user_id].attacks.append(user_guild)

    damage = raw_damage * stats.attack.value() * titan.armor
    tools.update_guild(guild_id=user_guild, stat="titan_damage", increase=damage)
    if G.USR[user_id].maximum_damage < damage:
        tools.update_stat(user_id=user_id, stat="maximum_damage", increase=damage)
        out.add(G.LOC.commands.attack.newrecord)
    remaining_hp = titan.hp - G.GLD[user_guild].titan_damage

    if G.GLD[user_guild].titan_damage >= titan.hp:
        if damage >= titan.hp:
            tools.update_stat(user_id=user_id, stat="instantkill", set=True)
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
        out.add(G.LOC.commands.attack.onkill.format(
            tools.fn(damage), max(round(titan.reward, 0), 1)
        ))
        return out.parse()
    else:
        out.add(G.LOC.commands.attack.onsuccess.format(
            tools.fn(damage), tools.fn(remaining_hp),
            round(remaining_hp / titan.hp * 100, 2)
        ))
        return out.parse()
    # We should never get here
    assert False, "Attack function did not escape correctly"


# Ascension -----------------------------------------------------------------
def tokens_from_joules(joules):
    return joules ** G.IDLE.ascension.exponent


def ascend_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.ascend.id):
        return True
    return False


def ascend_logic(message):
    user_id = str(message.author.id)
    out = tools.MsgBuilder()

    last_ascension_time = G.USR[user_id].ascension_time
    tools.update_stat(user_id=user_id, stat="ascension_time", set=time.time())
    elapsed = G.USR[user_id].ascension_time - last_ascension_time

    lifetime_joules = G.USR[user_id].lifetime_joules
    tokens = tokens_from_joules(lifetime_joules)

    min_joules = (
        G.IDLE.ascension.min_joules *
        G.IDLE.ascension.min_exp ** (G.USR[user_id].times_ascended + 1)
    )
    if lifetime_joules < min_joules:
        out.add(G.LOC.commands.ascend.notenough.format(
            tools.fn(min_joules), tools.fn(min_joules - lifetime_joules)))
        return out.parse()

    if elapsed > 30:
        out.add(G.LOC.commands.ascend.confirm.format(tokens))
        return out.parse()

    # Reset all statistics
    for stat in make_all_stats(user_id).values():
        stat.reset()

    # Reset all idle-related counter
    tools.update_stat(user_id=user_id, stat="joules", set=0)
    tools.update_stat(user_id=user_id, stat="sacrificed_joules", increase=lifetime_joules)
    tools.update_stat(user_id=user_id, stat="lifetime_joules", set=0)

    # increase tokens
    tools.update_stat(user_id=user_id, stat="tokens", increase=tokens)

    tools.update_stat(user_id=user_id, stat="times_ascended", increase=1)

    out.add(G.LOC.commands.ascend.success.format(
        tools.fn(lifetime_joules), tokens
    ))
    return out.parse()


def tierlist_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.tierlist.id):
        return True
    return False


def tierlist_logic(message):
    members = []
    out = tools.MsgBuilder()
    for member in message.author.guild.members:
        userId = str(member.id)
        members.append((userId, G.USR[userId].name, G.USR[userId].lifetime_joules))
    members = sorted(members, key=lambda tup: tup[2], reverse=True)
    try:
        out.add(G.LOC.commands.tierlist.rank1.format(
            members[0][1], tools.fn(members[0][2])
        ))
        out.add(G.LOC.commands.tierlist.rank2.format(
            members[1][1], tools.fn(members[1][2])
        ))
        out.add(G.LOC.commands.tierlist.rank3.format(
            members[2][1], tools.fn(members[2][2])
        ))
        top3 = [member[0] for member in members[:3]]
    except IndexError:
        return out.parse()
    if str(message.author.id) in top3:
        return out.parse()
    else:
        you = (str(message.author.id),
               G.USR[str(message.author.id)].name,
               G.USR[str(message.author.id)].lifetime_joules)
        out.add(G.LOC.commands.tierlist.rank_you.format(
            members.index(you) + 1,
            tools.fn(you[2])
        ))
        return out.parse()


def titan_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.titan.id):
        return True
    return False


def titan_logic(message):
    out = tools.MsgBuilder()
    if G.GLD[str(message.author.guild.id)].titan_status is False:
        out.add(G.LOC.commands.titan.notitan)
        return out.parse()
    level = G.GLD[str(message.author.guild.id)].titan_level
    damage_dealt = G.GLD[str(message.author.guild.id)].titan_damage
    titan = Titan(level)
    out.add(G.LOC.commands.titan.info.format(
        level,
        tools.fn(titan.hp),
        tools.fn(titan.hp - damage_dealt),
        round((titan.hp - damage_dealt) / titan.hp, 2),
        round((1 - titan.armor) * 100, 2),
        tools.fn(titan.reward)
    ))
    return out.parse()


def make_commands():
    tools.add_command(logic=harvest_logic, permission=harvest_perm)
    tools.add_command(logic=gamehelp_logic, permission=gamehelp_perm, where="user")
    tools.add_command(logic=upgrade_logic, permission=upgrade_perm)
    tools.add_command(logic=attack_logic, permission=attack_perm)
    tools.add_command(logic=ascend_logic, permission=ascend_perm)
    tools.add_command(logic=titan_logic, permission=titan_perm)
    tools.add_command(logic=tierlist_logic, permission=tierlist_perm)
