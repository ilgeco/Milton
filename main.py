import discord as ds
import tools
import commands
import game
import random
import globals as G
import munch as mun


def main(token, language, options_path):
    print("This is Milton, and I'm initializing.")
    client = ds.Client()

    G.initialize(options_path)
    commands.make_commands()
    game.make_achievements()

    # Completed loading of Milton message + preliminary activity
    @client.event
    async def on_ready():
        print('We have logged in as {0.user}.'.format(client))
        print('I will be speaking "{0}" as default.'.format(language))
        print("Looking for new members while I was away...")
        i = 0
        for guild in client.guilds:
            if str(guild.id) not in G.GLD.keys():
                defDict = {"language": language}
                G.GLD[str(guild.id)] = mun.DefaultMunch().fromDict(defDict, None)
            tools.save(G.OPT.guilds_path, G.GLD)
            for member in guild.members:
                if str(member.id) not in G.USR.keys():
                    i += 1
                    G.USR[str(member.id)] = mun.DefaultMunch(0)
                G.USR[str(member.id)].name = member.name
        tools.save_users()
        print(f"Found {i} new members")

        game = ds.Game("with myself.")
        print("Ready!")
        await client.change_presence(status=ds.Status.online, activity=game)

    # On message
    @client.event
    async def on_message(message):
        # Special checks on the message before parsing commands
        # Don't reply to yourself
        if message.author == client.user:
            return

        G.updateLOC(G.GLOC[G.GLD[str(message.guild.id)].language])

        # Randomly throw out an insult
        if message.content.startswith(G.OPT.prefix) is False and\
                G.OPT.insult_threshold is not False and\
                message.author != client.user:
            if G.OPT.insult_threshold == random.randint(0, G.OPT.insult_threshold):
                await message.channel.send(tools.get_random_line(G.LOC.randomInsult_path))

        # Don't compute further if it isn't a command.
        if message.content.startswith(G.OPT.prefix) is False:
            return

        # Count the number of times this person typed a command.
        tools.update_stat(user_id=message.author.id, stat="commandCount", increase=1)

        # Run normal commands
        for command in G.COMMANDS:
            if command.type == "message" and command.permission(message) is True:
                await message.channel.send(command.logic(message))

        # Check Achievements
        achieve_intro = True
        for achieve in G.ACHIEVES:
            if achieve.check_trigger(message, message.author.id) is True:
                out = tools.MsgBuilder()
                if achieve_intro:
                    out.add(G.LOC.msg.on_award)
                    achieve_intro = False
                out.add(achieve.award(message.author.id))
                await message.channel.send(out.msg)

    async def on_member_join(member):
        LOC = G.GLOC[G.GLD[str(member.guild.id)].language]
        if member.bot is True:
            # We don't do anything with bot accounts
            return

        for channel in member.server.channels:
            if str(channel.name).lower() in ['casa', 'general']:
                line = tools.get_random_line(LOC.hello_path)
                await channel.send(line.format(member.name))

        if member.id not in G.USR.keys():
            G.USR[str(member.id)] = mun.Munch()
            G.USR[str(member.id)].name = member.name
            tools.save_users()

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
