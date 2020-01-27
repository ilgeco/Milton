import discord as ds
from pathlib import Path
import tools
import random
import munch as mun


def main(token, language, options_path):
    print("This is Milton, and I'm initializing.")
    client = ds.Client()

    # Load options
    opt = tools.load(options_path)

    # Initialize guild and user files if non existent
    if Path(opt.users_path).exists() is False:
        print("Making a new users file. I was probably just installed.")
        tools.initialize_empty(opt.users_path)
    if Path(opt.guilds_path).exists() is False:
        print("Making a new guilds file. I was probably just installed.")
        tools.initialize_empty(opt.guilds_path)

    # Load locale, guild and user files
    gen_loc = tools.load(opt.locale_path)
    available_locales = gen_loc.keys()
    usr = tools.load(opt.users_path, default=None)
    gld = tools.load(opt.guilds_path, default=None)
    print("Options, locale and user files loaded. I remembered {0} users.".format(len(usr)))

    # Completed loading of Milton message + preliminary activity
    @client.event
    async def on_ready():
        print('We have logged in as {0.user}.'.format(client))
        print('I will be speaking "{0}" as default.'.format(language))
        print("Looking for new members while I was away...")
        i = 0
        for guild in client.guilds:
            if str(guild.id) not in gld.keys():
                defDict = {"language": language}
                gld[str(guild.id)] = mun.DefaultMunch().fromDict(defDict, None)
            tools.save(opt.guilds_path, gld)
            for member in guild.members:
                if str(member.id) not in usr.keys():
                    i += 1
                    usr[str(member.id)] = mun.Munch()
                usr[str(member.id)].name = member.name
        tools.save_users(opt, usr)
        print(f"Found {i} new members")

        game = ds.Game("with myself.")
        print("Ready!")
        await client.change_presence(status=ds.Status.online, activity=game)

    # On message
    @client.event
    async def on_message(message):
        loc = gen_loc[gld[str(message.guild.id)].language]

        if message.author == client.user:
            # Don't reply to yourself
            return

        if message.author == message.guild.owner and\
                message.content.startswith(opt.prefix + loc.commands.changeLang.id):
            prefixlength = len((opt.prefix + loc.commands.changeLang.id)) + 1
            query = message.content[prefixlength:(prefixlength + 2)].lower()
            if query in available_locales:
                gld[str(message.guild.id)].language = query
                loc = gen_loc[gld[str(message.guild.id)].language]
                tools.save(opt.guilds_path, gld)
                await message.channel.send(
                    loc.commands.changeLang.success.format(query.upper())
                )
            else:
                locales = " ".join(available_locales).upper()
                await message.channel.send(
                    loc.commands.changeLang.error.format(query, locales)
                )

        if message.content.startswith(opt.prefix) is False and\
                opt.insult_threshold is not False and\
                message.author != client.user:
            # Randomly throw out an insult
            if opt.insult_threshold == random.randint(0, opt.insult_threshold):
                await message.channel.send(tools.get_random_line(loc.randomInsult_path))

        if message.content.startswith(opt.prefix):
            # Count the number of times this person typed a command.
            if usr[str(message.author.id)].commandCount is None:
                usr[str(message.author.id)].commandCount = 1
            else:
                usr[str(message.author.id)].commandCount += 1
            tools.save_users(opt, usr)

        if message.content.startswith(opt.prefix + loc.commands.help.id):
            # Display help message
            helpmsg = loc.msg.help + "\n"
            for command in loc.commands.values():
                if command.showHelp is True:
                    helpmsg += (
                        "**" + opt.prefix + command.id + "**:\n\t" + command.help + "\n"
                    )
            await message.channel.send(helpmsg)

        if message.content.startswith(opt.prefix + loc.commands.random.id):
            # Give random fact
            fact = tools.get_random_line(loc.random_path)
            await message.channel.send(fact)

        if message.content.startswith(opt.prefix + loc.commands.userInfo.id):
            # Give user information
            strings = loc.commands.userInfo
            out = tools.MsgBuilder()
            out.add(strings.info)
            out.add(strings.userID.format(message.author.id))
            out.add(strings.guildID.format(
                message.author.guild.name, message.author.guild.id
            ))
            out.add(strings.commandCount.format(
                usr[str(message.author.id)].commandCount
            ))
            out.add(("> " + tools.get_random_line(loc.randomInfo_path)))
            await message.channel.send(out.msg)

        if message.content.startswith(opt.prefix + loc.commands.roll.id):
            # Roll random number
            prefixlength = len((opt.prefix + loc.commands.roll.id)) + 2
            try:
                print(message.content[prefixlength:])
                number = int(message.content[prefixlength:])
                await message.channel.send(loc.commands.roll.result.format(
                    sides=number,
                    result=random.randint(1, number)
                ))
            except ValueError:
                await message.channel.send(
                    loc.commands.roll.coercionError.format(
                        (opt.prefix + loc.commands.roll.id)
                    ))

    async def on_member_join(member):
        loc = gen_loc[gld[str(member.guild.id)].language]
        if member.bot is True:
            # We don't do anything with bot accounts
            return

        for channel in member.server.channels:
            if str(channel.name).lower() in ['casa', 'general']:
                line = tools.get_random_line(loc.hello_path)
                await channel.send(line.format(member.name))

        if member.id not in usr.keys():
            usr[str(member.id)] = mun.Munch()
            usr[str(member.id)].name = member.name
            tools.save_users(opt, usr)

    client.run(token)
    return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("token", help="Bot token", type=str)
    parser.add_argument("--optionsPath", "-o", help="Path to config file",
                        type=str, nargs="?", default="./options.json")
    parser.add_argument("--language", "-a", help="Language",
                        type=str, nargs="?", default="it")

    args = parser.parse_args()

    main(args.token,
         args.language,
         options_path=args.optionsPath)
