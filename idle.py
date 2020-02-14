"""This module contains all commands for the idle game inside of Milton."""
import globals as G
import tools
import munch
import time

from items import Inventory


class Statistic:
    """Calculate statistics value for a certain player based on the idle game settings.

    Takes into account player level to calculate value and costs.
    """
    def apply_items(self, number, level):
        a = number
        inventory = Inventory(self.user)
        if inventory.is_empty is not True:
            contents = sorted(inventory.content, key=lambda x: x.priority)
            for item in contents:
                if self.id in item.affected_stats and item.effect_level == level:
                    if item.effect_function == "additive":
                        number += item.base
                    elif item.effect_function == "multiplicative":
                        number *= item.base
                    else:
                        pass
        return number

    def __init__(self, identifier, user_id):
        """Creates statistic.

        Args:
            identifier: str
                Id of statistic as seen in the idle.json file.
            user_id: str
                Id of user to calculate statistic for - used to access users.json
        """
        self.id = identifier
        self.name = G.LOC.commands.upgrade.IDs[identifier]
        self.user = user_id
        # The name of the stat is normalized as "stat_level"
        self.stat_level = G.USR[user_id][identifier + "_level"]
        self.scaling = G.IDLE[identifier]
        self.prices = G.IDLE.prices[identifier]
        self.tokens = G.USR[user_id].tokens

        self.tokens_multiplier = 1 + (self.tokens / 100)

        # Update constants based on items owned
        self.scaling.base = self.apply_items(number=self.scaling.base, level="scaling.base")
        self.scaling.mult = self.apply_items(number=self.scaling.mult, level="scaling.mult")

        self.prices.base = self.apply_items(number=self.prices.base, level="prices.base")
        self.prices.mult = self.apply_items(number=self.prices.mult, level="prices.mult")

        def _calculate_price(myself, increase_level=0):
            """Calculate price to upgrade the stat.

            Args:
                increase_level: int
                    Increase the player level for the purpose of the calculation.
                    Defaults to 0.
            """
            if myself.prices.function == "exponential":
                return tools.exponential(
                    myself.prices.base,
                    myself.prices.mult,
                    myself.stat_level + increase_level
                )
            elif myself.prices.function == "linear":
                return tools.linear(
                    myself.prices.base,
                    myself.prices.mult,
                    myself.stat_level + increase_level
                )
            elif myself.prices.function == "log":
                return tools.logarithm(
                    myself.prices.base,
                    myself.prices.mult,
                    myself.stat_level + increase_level
                )
            elif myself.prices.function == "linear_mult":
                return tools.linear_multiplier(
                    myself.prices.base,
                    myself.prices.mult,
                    max(myself.stat_level + increase_level, 0),
                    G.IDLE[myself.id].level_mult,
                    G.IDLE[myself.id].level_threshold
                )
            else:
                raise ValueError("Unsupported formula type '{}'".format(
                    myself.prices.function))

        self.upgrade_price = _calculate_price(self)
        self.upgrade_price = self.apply_items(self.upgrade_price, level="price")
        self._price_fun = _calculate_price

    def recalculate_price(self, increase_level=0):
        return self._price_fun(self, increase_level)

    def value(self, increase_level=0):
        """Calculate the value of the statistic.

        Also takes into account items owned by the user.

        increase_level: int
            Increase the player level for the purpose of the calculation.
            Defaults to 0.
        """
        if self.scaling.function == "exponential":
            value = tools.exponential(
                self.scaling.base,
                self.scaling.mult,
                max(self.stat_level + increase_level, 0)
            )
        elif self.scaling.function == "linear":
            value = tools.linear(
                self.scaling.base,
                self.scaling.mult,
                max(self.stat_level + increase_level, 0)
            )
        elif self.scaling.function == "log":
            value = tools.logarithm(
                self.scaling.base,
                self.scaling.mult,
                max(self.stat_level + increase_level, 0)
            )
        elif self.scaling.function == "linear_mult":
            value = tools.linear_multiplier(
                self.scaling.base,
                self.scaling.mult,
                max(self.stat_level + increase_level, 0),
                G.IDLE[self.id].level_mult,
                G.IDLE[self.id].level_threshold
            )
        else:
            raise ValueError("Unsupported formula type '{}'".format(
                self.prices.function))

        value *= self.tokens_multiplier

        # Apply item effects at value level
        value = self.apply_items(number=value, level="value")

        return value

    def upgrade(self, value=1):
        """Award the player some level in this stat."""
        tools.update_user(self.user, self.id + "_level", increase=value)

    def downgrade(self, value=1):
        """Reduce the player level by some value."""
        tools.update_user(self.user, self.id + "_level", increase=-value)

    def reset(self):
        """Reset this stat to level 0"""
        tools.update_user(self.user, self.id + "_level", set=0)


# Game Help ------------------------------------------------------------------
def game_help_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.gameHelp.id):
        return True
    return False


def game_help_logic(message):
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
    """Handles all idle game updates based on time and returns appropriate message to push to chat."""
    # Simplify my life - partial variable unpacking
    user_id = str(message.author.id)
    output = tools.MsgBuilder()

    current_time = time.time()
    last_time = G.USR[user_id].last_harvest
    tools.update_user(user_id=user_id, stat="last_harvest", set=current_time)

    # Leave this as clutter free as possible for eventual additional uses
    # >> Produce Joules
    output.add(produce_joules(user_id, current_time, last_time))

    tools.save_users()
    return output.parse()


def produce_joules(user_id, current_time, last_time):
    """Handles calculating joules to add as well generating the message to push to chat.

    Also appropriately updates user dictionaries on joules produced.
    """
    output = tools.MsgBuilder()
    inventory = Inventory(user_id)

    production = Statistic("production", user_id)
    maxTicks = Statistic("maxTicks", user_id)

    if last_time == 0:
        # I give a gift of some joules for the uninitialized user.
        tools.update_user(user_id=user_id, stat="joules", set=G.IDLE.harvest.gift)
        return G.LOC.commands.harvest.firstTime.format(
            G.IDLE.harvest.gift, round((G.IDLE.production.base * 60), 0))
    else:
        production_time = current_time - last_time
        bonsai_time = production_time

        if production_time > maxTicks.value():
            production_time = maxTicks.value()
            output.add(G.LOC.commands.harvest.overproduced.format(
                G.OPT.prefix + G.LOC.commands.upgrade.id))

        joules_produced = production_time * production.value()
        joules_produced *= G.IDLE.harvest.achievebonus ** tools.count_achieves(user_id)
        if inventory.contains("joules_bonsai"):
            bonsai_joules = bonsai_time * G.IDLE["items"].joules_bonsai.base * production.value()\
                               * G.IDLE.harvest.achievebonus ** tools.count_achieves(user_id)
            out.add(G.LOC["items"].joules_bonsai.activation.format(
                tools.fn(bonsai_joules)
            ))

        tools.update_user(user_id=user_id, stat="joules", increase=joules_produced)
        tools.update_user(user_id=user_id, stat="lifetime_joules", increase=joules_produced)

        output.add(G.LOC.commands.harvest.production.format(
            tools.fn(joules_produced),
            tools.fn(G.USR[user_id].joules)
        ))
        return output.parse()


# Upgrade stat -------------------------------------------------------------
def upgrade_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.upgrade.id):
        return True
    return False


def upgrade_logic(message):
    """Used to upgrade a certain statistic's level.

    Should automatically allow increasing level of stat in the idle.json file.
    """
    user_id = str(message.author.id)
    out = tools.MsgBuilder()

    # No arguments were given.
    # TODO: Can change to just use MsgParser? Or just make it send the help message
    if len(message.content.split(" ")) == 1:
        out.add(G.LOC.commands.upgrade.notrecognized.format(
            ", ".join(G.LOC.commands.upgrade.IDs.values()).rstrip(', ')))
        return out.parse()

    message = tools.MsgParser(message.content)
    stats = make_all_stats(user_id)
    stat_names = [stat.name for stat in stats.values()]
    current_joules = G.USR[user_id].joules

    if message.args[0] == G.LOC.commands.upgrade.IDs.info:
        # Send information message
        out.add(G.LOC.commands.upgrade.info)
        # >> Upgrade max ticks help
        out.add(G.LOC.commands.upgrade.upgradable.maxTicks.format(
            G.LOC.commands.upgrade.IDs.maxTicks,
            tools.fn(stats.maxTicks.value() / 3600),
            tools.fn(stats.maxTicks.value(1) / 3600),
            tools.fn(stats.maxTicks.upgrade_price)
        ).split("|"))
        if stats.maxTicks.upgrade_price <= current_joules:
            out.append(" < OK!")
        # >> Upgrade production help
        out.add(G.LOC.commands.upgrade.upgradable.production.format(
            G.LOC.commands.upgrade.IDs.production,
            tools.fn(stats.production.value() * 60),
            tools.fn(stats.production.value(1) * 60),
            tools.fn(stats.production.upgrade_price)
        ).split("|"))
        if stats.production.upgrade_price <= current_joules:
            out.append(" < OK!")
        # >> Upgrade attack help
        out.add(G.LOC.commands.upgrade.upgradable.attack.format(
            G.LOC.commands.upgrade.IDs.attack,
            tools.fn(stats.attack.value()),
            tools.fn(stats.attack.value(1)),
            tools.fn(stats.attack.upgrade_price)
        ).split("|"))
        if stats.attack.upgrade_price <= current_joules:
            out.append(" < OK!")

        return out.pretty_parse()

    elif message.args[0] in stat_names:
        # If a correct stat was parsed
        try:
            # Attempt of getting a number of times to upgrade. If we fail, just upgrade it once.
            times = int(message.args[1])
            if times <= 0:
                times = 1
            if times > 100:
                times = 100
        except (ValueError, IndexError):
            times = 1

        i = 0
        total_spent = 0
        stopped_early = False
        upgraded_once = False
        stats = make_all_stats(user_id)
        stat = [x for x in stats.values() if x.name == message.args[0]][0]
        price = stat.upgrade_price
        while i < times:
            if G.USR[user_id].joules >= price:
                upgraded_once = True
                # Enough joules to update
                stat.upgrade()
                tools.update_user(user_id=user_id, stat="joules", increase=-stat.upgrade_price)
                total_spent += price
                price = stat.recalculate_price(increase_level=(i + 1))
            else:
                # I don't add the out.add() command here for the order of the messages (I'm lazy)
                stopped_early = True
                break
            i += 1

        if upgraded_once:
            out.add(G.LOC.commands.upgrade.onsuccess.format(
                tools.fn(total_spent),
                stat.name,
                i
            ))
        if stopped_early:
            out.add(G.LOC.commands.upgrade.onfailure.format(
                tools.fn(G.USR[user_id].joules),
                stat.name,
                tools.fn(price)
            ))

        return out.parse()

    else:
        # If we didn't recognize the stat given.
        out.add(G.LOC.commands.upgrade.notrecognized.format(
            ", ".join(G.LOC.commands.upgrade.IDs.values()).rstrip(', '))
        )
        return out.parse()


def make_all_stats(user_id: str) -> munch:
    """Generates all statistics that a user can have.

    Uses the available stat names in idle.json (under "prices") in a munch dictionary.
    """
    stats = munch.Munch()
    for stat in G.IDLE.prices:
        stats[stat] = Statistic(stat, user_id)
    return stats


# Attack ------------------------------------------------------------------
class Titan:
    """Used to calculate initial values for titans"""
    def __init__(self, level):
        self.level = level
        self.hp = level ** G.IDLE.titan.level_exp * G.IDLE.titan.base_hp
        # This is a function that tends to 0 @ level -> inf
        # The smaller the armor constant the slower the armor grows.
        b = G.IDLE.titan.armor_constant
        self.armor = 1 / (b * (self.level ** 2) + 1)
        self.base_reward = level ** G.IDLE.titan.reward_constant / self.armor


def spawn_titan(guild):
    """Spawns a titan in the current guild.

    Returns:
        int - Level of the spawned titan.
    """
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
    """Handles attacking titans.

    Returns:
        String to push to chat.
    """
    user_id = str(message.author.id)
    inventory = Inventory(user_id)
    user_guild = str(message.author.guild.id)
    out = tools.MsgBuilder()

    # If we don't have any titans, we cannot attack.
    if G.GLD[user_guild].titan_status is not True:
        out.add(G.LOC.commands.attack.notitan)
        return out.parse()

    # Cannot attack more than once every xx hours:
    now = time.time()
    elapsed = now - G.USR[user_id].last_attack
    wait_time = G.IDLE.titan.min_hours * 3600
    if inventory.contains("sword_of_storms"):
        wait_time /= 10
    if elapsed < wait_time:
        out.add(G.LOC.commands.attack.toosoon.format(
            round((wait_time - elapsed) / 3600, 2)
        ))
        return out.parse()
    tools.update_user(user_id, "last_attack", set=now)
    stats = make_all_stats(user_id)
    titan = Titan(G.GLD[user_guild].titan_level)

    if isinstance(G.USR[user_id].attacks, list) is False:
        # User has never attacked before - initialize them
        G.USR[user_id].attacks = []

    if user_guild not in G.USR[user_id].attacks:
        # Remember that the user attacked.
        G.USR[user_id].attacks.append(user_guild)

    damage = stats.attack.value() * titan.armor

    if inventory.contains("hand_of_midas"):
        tools.update_user(user_id, "joules", increase=damage/2)
        out.add(G.LOC["items"].hand_of_midas.activation.format(
            tools.fn(damage/2)
        ))

    tools.update_user(user_id=user_id, stat="titan_damage", increase=damage)
    tools.update_guild(guild_id=user_guild, stat="titan_damage", increase=damage)
    tools.update_user(user_id=user_id, stat="times_attacked", increase=1)

    remaining_hp = titan.hp - G.GLD[user_guild].titan_damage

    if G.GLD[user_guild].titan_damage >= titan.hp:
        # The titan was killed by this attack
        # Check achievement
        if damage >= titan.hp:
            tools.update_user(user_id=user_id, stat="instantkill", set=True)

        tools.update_guild(guild_id=user_guild, stat="titan_status", set=False)

        # Check all players to see if we need to reward them tokens.
        for key, user in G.USR.items():
            if isinstance(user.attacks, list) is False:
                continue
            if user_guild in user.attacks:
                # Award tokens to this player.
                G.USR[key].tokens += max(round(titan.base_reward, 0), 1)
                G.USR[key].tokens += max(calculate_token_reward(G.USR[key].titan_damage), 0)
                G.USR[key].titan_damage = 0
                G.USR[key].attacks.remove(user_guild)

        tools.save_users()
        out.add(G.LOC.commands.attack.onkill.format(
            tools.fn(damage), max(round(titan.base_reward, 0), 1)
        ))
        return out.parse()
    else:
        out.add(G.LOC.commands.attack.onsuccess.format(
            tools.fn(damage), tools.fn(remaining_hp),
            round(remaining_hp / titan.hp * 100, 2)
        ))
        return out.parse()


def calculate_token_reward(joules):
    """Formula used to calculate tokens to reward players when killing titans."""
    return round(joules ** G.IDLE.titan.reward_damage_exponent, 0)


# Ascension -----------------------------------------------------------------
def tokens_from_joules(joules):
    return joules ** G.IDLE.ascension.exponent


def ascend_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.ascend.id):
        return True
    return False


def ascend_logic(message):
    """Ascends user and awards tokens."""
    user_id = str(message.author.id)
    out = tools.MsgBuilder()

    # Handles timings (this command should be sent twice quickly)
    last_ascension_time = G.USR[user_id].ascension_time
    tools.update_user(user_id=user_id, stat="ascension_time", set=time.time())
    elapsed = G.USR[user_id].ascension_time - last_ascension_time
    # Unpack some variables
    lifetime_joules = G.USR[user_id].lifetime_joules
    tokens = tokens_from_joules(lifetime_joules)
    bonus_tokens = 0
    # Handle awarding bonus tokens as indicated in idle.json (ascension.bonus)
    if G.USR[user_id].times_ascended <= len(G.IDLE.ascension.bonus):
        bonus_tokens = G.IDLE.ascension.bonus[max(G.USR[user_id].times_ascended - 1, 0)]
    # Calculate minimum number of joules to have when ascending.
    min_joules = (
        G.IDLE.ascension.min_joules *
        G.IDLE.ascension.min_exp ** (G.USR[user_id].times_ascended + 1))
    if lifetime_joules < min_joules:
        # Not enough joules produced.
        out.add(G.LOC.commands.ascend.notenough.format(
            tools.fn(min_joules), tools.fn(min_joules - lifetime_joules)))
        return out.parse()

    if elapsed > G.IDLE.ascension.elapsed:
        # Command was sent too long ago. Send "Are you sure?"
        if bonus_tokens == 0:
            out.add(G.LOC.commands.ascend.confirm.format(tokens))
        else:
            out.add(G.LOC.commands.ascend.confirm_bonus.format(
                tokens, bonus_tokens
            ))
        return out.parse()

    # If we get here, we are ascending.
    # Reset all statistics
    for stat in make_all_stats(user_id).values():
        if stat.id != "attack":
            # Don't reset attack statistic
            stat.reset()

    # Reset all idle-related counter
    tools.update_user(user_id=user_id, stat="joules", set=0)
    tools.update_user(user_id=user_id, stat="sacrificed_joules", increase=lifetime_joules)
    tools.update_user(user_id=user_id, stat="lifetime_joules", set=0)

    # increase tokens
    tools.update_user(user_id=user_id, stat="tokens", increase=(tokens + bonus_tokens))

    tools.update_user(user_id=user_id, stat="times_ascended", increase=1)

    out.add(G.LOC.commands.ascend.success.format(
        tools.fn(lifetime_joules), tokens
    ))

    return out.parse()


# User tier list for a certain server --------------------------------------------------------
def tier_list_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.tierlist.id):
        return True
    return False


def tier_list_logic(message):
    """Gives tier list message to push to chat.

    If the user is not in the top-three, also sends their position.
    """
    members = []
    out = tools.MsgBuilder()
    for member in message.author.guild.members:
        # Extract all members of the guild for manipulation
        user_id = str(member.id)
        members.append(
            (user_id,
             G.USR[user_id].name,
             G.USR[user_id].lifetime_joules + G.USR[user_id].sacrificed_joules)
        )
    # Order based on lifetime joules produced.
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
        # There are less than 3 members in the server, just stop early and parse.
        return out.parse()
    if str(message.author.id) in top3:
        # The user is already included in the top 3 users.
        return out.parse()
    else:
        # Also send the user's position in the leader board
        you = (str(message.author.id),
               G.USR[str(message.author.id)].name,
               G.USR[str(message.author.id)].lifetime_joules +
               G.USR[str(message.author.id)].sacrificed_joules)
        out.add(G.LOC.commands.tierlist.rank_you.format(
            members.index(you) + 1,
            tools.fn(you[2])
        ))
        return out.parse()


# Displays information about titans ------------------------------------------------------------
def titan_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.titan.id):
        return True
    return False


def titan_logic(message):
    """Handles retrieving information about titans and giving a message to push to chat."""
    out = tools.MsgBuilder()
    user_id = str(message.author.id)

    if G.GLD[str(message.author.guild.id)].titan_status is False:
        # There is no titan.
        out.add(G.LOC.commands.titan.notitan)
        return out.parse()

    level = G.GLD[str(message.author.guild.id)].titan_level
    damage_dealt = G.GLD[str(message.author.guild.id)].titan_damage
    titan = Titan(level)

    out.add(G.LOC.commands.titan.info.format(
        level,
        tools.fn(titan.hp),
        tools.fn(titan.hp - damage_dealt),
        round((titan.hp - damage_dealt) / titan.hp * 100, 2),
        round((1 - titan.armor) * 100, 2),
        tools.fn(titan.base_reward + calculate_token_reward(G.USR[user_id].titan_damage))
    ))
    return out.parse()


def make_commands():
    """Makes all commands relative to this module"""
    tools.add_command(logic=harvest_logic, permission=harvest_perm)
    tools.add_command(logic=game_help_logic, permission=game_help_perm, where="user")
    tools.add_command(logic=upgrade_logic, permission=upgrade_perm)
    tools.add_command(logic=attack_logic, permission=attack_perm)
    tools.add_command(logic=ascend_logic, permission=ascend_perm)
    tools.add_command(logic=titan_logic, permission=titan_perm)
    tools.add_command(logic=tier_list_logic, permission=tier_list_perm)
