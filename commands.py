import globals as G
import tools
from mpmath import *
from idle import make_all_stats, tokens_from_joules
from items import Inventory
import random
import asyncio
import games
from threading import Lock


# I divided permissions and command logic due to the necessity of using
# await in the main script. So I can first check the if (in the loop) and,
# if the if resolves, I generate the necessary message using the command logic
# and send it out using a single await statement.


# help ---------------------------------
# Send help for every command available to Milton
def help_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.help.id):
        return True
    return False


def help_logic(message):
    out = tools.MsgBuilder()
    out.add(G.LOC.msg.help)
    for command in G.LOC.commands.values():
        if command.showHelp is True and "general" in command.category:
            out.add(
                "**" + G.OPT.prefix + command.id + "**:\n\t" + command.help
            )
    return out.parse()


# Set notification channel ----------------------------------------------------
# Set the default notification channel to send messages to in this guild. Only for server owners.
def set_notification_channel_perm(message):
    if message.author == message.guild.owner and\
            message.content.startswith(G.OPT.prefix + G.LOC.commands.setnotification.id):
        return True
    return False


def set_notification_channel_logic(message):
    out = tools.MsgBuilder()
    if G.GLD[str(message.author.guild.id)].notification_channel != message.channel.id:
        G.GLD[str(message.author.guild.id)].notification_channel = message.channel.id
        tools.save_guilds()
        out.add(G.LOC.commands.setnotification.notificationsenabled)
        return out.parse()
    else:
        G.GLD[str(message.author.guild.id)].notification_channel = 0
        tools.save_guilds()
        out.add(G.LOC.commands.setnotification.notificationsdisabled)
        return out.parse()


# Change Language ---------------------------------
# Change Milton's preferred language for this server. Only for server owners.
def change_language_perm(message):
    if message.author == message.guild.owner and\
            message.content.startswith(G.OPT.prefix + G.LOC.commands.changeLang.id):
        return True
    return False


def change_language_logic(message):
    prefix_length = len((G.OPT.prefix + G.LOC.commands.changeLang.id)) + 1
    query = message.content[prefix_length:(prefix_length + 2)].lower()
    available_locales = G.GLOC.keys()
    out = tools.MsgBuilder()
    if query in available_locales:
        G.GLD[str(message.guild.id)].language = query
        tools.save(G.OPT.guilds_path, G.GLD)
        G.update_loc(G.GLOC[G.GLD[str(message.guild.id)].language])
        out.add(
            G.LOC.commands.changeLang.success.format(query.upper())
        )
        return out.parse()
    else:
        locales = " ".join(available_locales).upper()
        out.add(
            G.LOC.commands.changeLang.error.format(query, locales)
        )
        return out.parse()


# Give random fact ----------------------------------------------------------
# Show a random fact from the random text file
def random_fact_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.random.id):
        return True
    return False


def random_fact_logic(message):
    out = tools.MsgBuilder()
    tools.update_user(message.author.id, stat="factCount", increase=1)
    tools.save_users()
    out.add(tools.get_random_line(G.LOC.random_path))
    return out.parse()


# Give user info ------------------------------------------------------------
# Return information about the user.
def user_info_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.userInfo.id):
        return True
    return False


def user_info_logic(message):
    user_id = str(message.author.id)
    stats = make_all_stats(user_id)
    # Give user information
    strings = G.LOC.commands.userInfo
    out = tools.MsgBuilder()
    bonus_tokens = 0
    inventory = Inventory(user_id)

    if G.USR[user_id].times_ascended <= len(G.IDLE.ascension.bonus):
        bonus_tokens = G.IDLE.ascension.bonus[G.USR[user_id].times_ascended]

    # Introduction to help message
    out.add(strings.info)
    # Information about joules and lifetime joules
    out.add(strings.joules.format(
        tools.fn(G.USR[user_id].joules, decimals=2),
        tools.fn(G.USR[user_id].lifetime_joules, decimals=2))
    )
    # Information about tokens, token effects, and tokens gained on ascension.
    out.add(strings.tokens.format(
        tools.fn(G.USR[user_id].tokens, decimals=1),
        tools.fn(1 + (log(1 + G.USR[user_id].tokens, 10))),
        tools.fn(tokens_from_joules(G.USR[user_id].lifetime_joules)),
        tools.fn(bonus_tokens, decimals=1)
    ))
    # Information about matter level
    if G.USR[user_id].epoch >= 1 and G.USR[user_id].matter > 0:
        out.add(strings.matterlevel.format(
            tools.fn(G.USR[user_id].matter)
        ))
    # Information about lifetime statistics
    out.add(strings.lifetime.format(
        G.USR[user_id].times_ascended,
        tools.fn(G.USR[user_id].sacrificed_joules)
    ))
    # Information about "production" stat
    out.add(strings.productionlevel.format(
        stats.production.stat_level,
        tools.fn(stats.production.value() * 60, decimals=1)
    ))
    # Information about "time" stat
    out.add(strings.timelevel.format(
        stats.time.stat_level,
        tools.fn(stats.time.value())
    ))
    # Information about "attack" stat
    out.add(strings.attacklevel.format(
        stats.attack.stat_level,
        tools.fn(stats.attack.value())
    ))
    # Information about "commandCount" stat
    out.add(strings.commandCount.format(
        G.USR[str(message.author.id)].commandCount
    ))
    # Information about items in inventory.
    items = ", ".join([G.LOC["items"][item.id].name for item in inventory.content])
    items = items.rstrip()
    if items == "":
        out.add(strings.noitems)
    else:
        out.add(strings["items"].format(
            items
        ))
    # Information about achievements
    out.add(strings.achieves.format(
        tools.count_achieves(user_id),
        round(G.IDLE.harvest.achievebonus ** tools.count_achieves(user_id), 2)
    ))
    # Random funny line.
    out.add(("> " + tools.get_random_line(G.LOC.randomInfo_path)))

    return out.parse()




def pacinco_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.pacinco.id):
        return True
    return False

lock=Lock()
async def pacinco_logic(message):
    if not lock.acquire(False):
        return
    else:
        try:      
            out = tools.MsgBuilder()
            user_id = str(message.author.id)    
            arg = tools.MsgParser(message.content)
            value = mpf(arg.args[0])
            jl = G.USR[user_id]["joules"]
            if value<0 or value>jl:
                out.add("Negativo!")
                await message.channel.send(out.parse()[0])
                return       
            
            pac = games.Pacinco()
            toout, victory = pac.play()
            sent = await message.channel.send(toout[0])
            for i in toout[1:]:                    
                await sent.edit(content=i)
                await asyncio.sleep(0.5)                
            gain = victory*value-value
            jl = G.USR[user_id]["joules"]
            if value > jl:
                out.add("Negativo!")
                await message.channel.send(out.parse()[0])
                return  
            tools.update_user(user_id=user_id, stat="joules", set=jl+gain)
            out.add(G.LOC.games.pacinco_win.format(G.USR[user_id].name, nstr(gain,5), nstr(jl+gain,5)))    
            await message.channel.send(out.parse()[0])
        finally:
         lock.release()
    





# Roll random number -------------------------------------------------------
def roll_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.roll.id):
        return True
    return False


def roll_logic(message):
    prefix_length = len((G.OPT.prefix + G.LOC.commands.roll.id)) + 2
    out = tools.MsgBuilder()
    try:
        number = int(message.content[prefix_length:])
        outcome = random.randint(1, number)
        # Check for achievements
        if number == 20 and outcome == 20:
            tools.update_user(message.author.id, stat="gotLucky", set=True)
        if number == 20 and outcome == 1:
            tools.update_user(message.author.id, stat="gotUnlucky", set=True)

        out.add(G.LOC.commands.roll.result.format(
            sides=number,
            result=outcome
        ))
        return out.parse()
    except ValueError:
        out.add(G.LOC.commands.roll.coercionError.format(
            (G.OPT.prefix + G.LOC.commands.roll.id)
        ))
        return out.parse()


# Achievement Help ----------------------------------------------------------
# Give all not-secret achievements descriptions + achieved commands.
# This should automatically detect all commands in the localization file.
def help_achieve_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.help_achieve.id):
        return True
    return False


def help_achieve_logic(message):
    user_info = G.USR[str(message.author.id)]
    help_msg = tools.MsgBuilder()
    help_msg.add(G.LOC.commands.help_achieve.intro)
    i = 0
    for key, achieve in G.LOC.achievements.items():
        # TODO: This is rather ugly.
        achievement = [x for x in G.ACHIEVES if x.id == key][0]
        if achievement.status == "legacy" and user_info[key] in [False, 0]:
            # We ignore legacy achievements that have not been unlocked by the user.
            continue
        if achieve.include_help or user_info[key]:
            if user_info[key]:
                help_msg.add(G.LOC.msg.format_yes.format(
                    G.LOC.achievements[key].name,
                    G.LOC.achievements[key].condition
                ))
            else:
                help_msg.add(G.LOC.msg.format_no.format(
                    G.LOC.achievements[key].name,
                    G.LOC.achievements[key].condition
                ))
        if achieve.include_help is False and user_info[key] in [False, 0]:
            i += 1
    help_msg.add(G.LOC.msg.secret_achieves.format(i))
    return help_msg.parse()


# Short help just sends a list of achieves in chat, without descriptions.
def short_help_achieve_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.help_achieve_short.id):
        return True
    return False


def short_help_achieve_logic(message):
    user_info = G.USR[str(message.author.id)]
    help_msg = tools.MsgBuilder()
    help_msg.add(G.LOC.commands.help_achieve_short.intro)
    for key, achieve in G.LOC.achievements.items():
        if user_info[key]:
            help_msg.append(G.LOC.msg.format_short.format(
                G.LOC.achievements[key].name
            ), sep=" ")
    return help_msg.parse()


# Package all commands in one place --------------------------------
def make_commands():
    tools.add_command(logic=pacinco_logic, permission=pacinco_perm)
    tools.add_command(logic=help_logic, permission=help_perm, where="user")
    tools.add_command(logic=help_achieve_logic, permission=help_achieve_perm, where="user")
    tools.add_command(logic=change_language_logic, permission=change_language_perm)
    tools.add_command(logic=random_fact_logic, permission=random_fact_perm)
    tools.add_command(logic=user_info_logic, permission=user_info_perm)
    tools.add_command(logic=roll_logic, permission=roll_perm)
    tools.add_command(logic=set_notification_channel_logic, permission=set_notification_channel_perm)
    tools.add_command(logic=short_help_achieve_logic, permission=short_help_achieve_perm)
