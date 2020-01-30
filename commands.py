import globals as G
import tools
import random


class Command():
    def __init__(self, logic, permission, ctype):
        self.logic = logic
        self.type = ctype
        if permission is False:
            self.permission = True
        else:
            self.permission = permission


# help ---------------------------------
def help_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.help.id):
        return True
    return False


def help_logic(message):
    helpmsg = G.LOC.msg.help + "\n"
    for command in G.LOC.commands.values():
        if command.showHelp is True:
            helpmsg += (
                "**" + G.OPT.prefix + command.id + "**:\n\t" + command.help + "\n"
            )
    return helpmsg


# Change Language ---------------------------------
def changeLang_perm(message):
    if message.author == message.guild.owner and\
            message.content.startswith(G.OPT.prefix + G.LOC.commands.changeLang.id):
        return True
    return False


def changeLang_logic(message):
    prefixlength = len((G.OPT.prefix + G.LOC.commands.changeLang.id)) + 1
    query = message.content[prefixlength:(prefixlength + 2)].lower()
    available_locales = G.GLOC.keys()
    if query in available_locales:
        G.GLD[str(message.guild.id)].language = query
        tools.save(G.OPT.guilds_path, G.GLD)
        G.updateLOC(G.GLOC[G.GLD[str(message.guild.id)].language])
        return G.LOC.commands.changeLang.success.format(query.upper())
    else:
        locales = " ".join(available_locales).upper()
        return G.LOC.commands.changeLang.error.format(query, locales)


# Give random fact ----------------------------------------------------------
def randomFact_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.random.id):
        return True
    return False


def randomFact_logic(message):
    tools.update_stat(message.author.id, stat="factCount", increase=1)
    tools.save_users()
    return tools.get_random_line(G.LOC.random_path)


# Give user info ------------------------------------------------------------
def userInfo_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.userInfo.id):
        return True
    return False


def userInfo_logic(message):
    # Give user information
    strings = G.LOC.commands.userInfo
    out = tools.MsgBuilder()
    out.add(strings.info)
    out.add(strings.userID.format(message.author.id))
    out.add(strings.guildID.format(
        message.author.guild.name, message.author.guild.id
    ))
    out.add(strings.commandCount.format(
        G.USR[str(message.author.id)].commandCount
    ))
    out.add(("> " + tools.get_random_line(G.LOC.randomInfo_path)))
    return out.msg


# Roll random number
def roll_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.roll.id):
        return True
    return False


def roll_logic(message):
    prefixlength = len((G.OPT.prefix + G.LOC.commands.roll.id)) + 2
    try:
        number = int(message.content[prefixlength:])
        outcome = random.randint(1, number)
        # Check for achievements
        if number == 20 and outcome == 20:
            tools.update_stat(message.author.id, stat="gotLucky", set=True)
            tools.save_users()
        if number == 20 and outcome == 1:
            tools.update_stat(message.author.id, stat="gotUnlucky", set=True)
            tools.save_users()
        return G.LOC.commands.roll.result.format(
            sides=number,
            result=outcome
        )
    except ValueError:
        return G.LOC.commands.roll.coercionError.format(
            (G.OPT.prefix + G.LOC.commands.roll.id)
        )


# help ---------------------------------
def help_achieve_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.help_achieve.id):
        return True
    return False


def help_achieve_logic(message):
    userInfo = G.USR[str(message.author.id)]
    helpmsg = tools.MsgBuilder()
    helpmsg.add(G.LOC.commands.help_achieve.intro)
    for key, achieve in G.LOC.achievements.items():
        if achieve.include_help or userInfo[key]:
            if userInfo[key]:
                helpmsg.add(G.LOC.msg.format_yes.format(
                    G.LOC.achievements[key].name,
                    G.LOC.achievements[key].condition
                ))
            else:
                helpmsg.add(G.LOC.msg.format_no.format(
                    G.LOC.achievements[key].name,
                    G.LOC.achievements[key].condition
                ))
    return helpmsg.msg


def add_command(logic, permission, ctype):
    G.COMMANDS.append(Command(logic, permission, ctype))


def make_commands():
    add_command(
        logic=help_logic, permission=help_perm, ctype="message")
    add_command(
        logic=help_achieve_logic, permission=help_achieve_perm, ctype="message")
    add_command(
        logic=changeLang_logic, permission=changeLang_perm, ctype="message")
    add_command(
        logic=randomFact_logic, permission=randomFact_perm, ctype="message")
    add_command(
        logic=userInfo_logic, permission=userInfo_perm, ctype="message")
    add_command(
        logic=roll_logic, permission=roll_perm, ctype="message")
