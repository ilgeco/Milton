import discord as ds
import tools
import commands
import time
import asyncio
import idle
import achieves
import random
import globals as G
import munch as mun
import logging

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


def main(token, language, options_path):
    """Main Milton subroutine.

    Loads all modules, memory, and handles incoming messages.
    """

    print("This is Milton, and I'm initializing.")
    client = ds.Client()

    G.initialize(options_path)
    commands.make_commands()
    achieves.make_achievements()
    idle.make_commands()

    # Completed loading of Milton message + preliminary activity
    @client.event
    async def on_ready():
        print('We have logged in as {0.user}.'.format(client))
        print('I will be speaking "{0}" as default.'.format(language))

        print("Looking for new members/guilds while I was away...")
        # We search all guilds and users Milton can see and initialize them.
        i = 0
        for guild in client.guilds:
            # Add new guilds
            if str(guild.id) not in G.GLD.keys():
                defDict = {"language": language}
                G.GLD[str(guild.id)] = mun.DefaultMunch().fromDict(defDict, 0)
            tools.save(G.OPT.guilds_path, G.GLD)
            # Add new members
            for member in guild.members:
                if str(member.id) not in G.USR.keys():
                    i += 1
                    G.USR[str(member.id)] = mun.DefaultMunch(0)
                G.USR[str(member.id)].name = member.name
        tools.save_users()
        print(f"Found {i} new members")

        game = ds.Game("with myself.")  # Update "playing" message, for fun.
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

        # Update total joules (remove in a while?):
        if G.USR[str(message.author.id)].lifetime_joules == 0 and \
                G.USR[str(message.author.id)].joules > 0:
            stats = idle.make_all_stats(str(message.author.id))
            min_joules = G.USR[str(message.author.id)].joules
            for stat in stats.values():
                min_joules += stat.recalculate_price(-1)
            tools.update_stat(str(message.author.id), stat="lifetime_joules", set=min_joules)

        # Run normal commands
        for command in G.COMMANDS:
            if command.permission(message) is True:
                if command.where == "channel":
                    for string in command.logic(message):
                        await message.channel.send(string)
                elif command.where == "user":
                    if message.author.dm_channel is None:
                        await message.author.create_dm()
                    for string in command.logic(message):
                        await message.author.dm_channel.send(string)
                    await message.delete()

        # Check Achievements
        achieve_intro = True
        for achieve in G.ACHIEVES:
            if achieve.check_trigger(str(message.author.id)) is True:
                out = tools.MsgBuilder()
                if achieve_intro:
                    out.add(G.LOC.msg.on_award)
                    achieve_intro = False
                out.add(achieve.award(message.author.id))
                for string in out.parse():
                    await message.channel.send(string)

    async def on_member_join(member):
        G.updateLOC(G.GLOC[G.GLD[str(member.guild.id)].language])
        if member.bot is True:
            # We don't do anything with bot accounts
            return

        for channel in member.server.channels:
            if str(channel.name).lower() in ['casa', 'general']:
                line = tools.get_random_line(G.LOC.hello_path)
                await channel.send(line.format(member.name))

        if member.id not in G.USR.keys():
            G.USR[str(member.id)] = mun.DefaultMunch(0)
            G.USR[str(member.id)].name = member.name
            tools.save_users()

    async def on_guild_join(guild):
        if str(guild.id) not in G.GLD.keys():
            defDict = {"language": language}
            G.GLD[str(guild.id)] = mun.DefaultMunch().fromDict(defDict, 0)
        tools.save(G.OPT.guilds_path, G.GLD)
        # Add new members
        for member in guild.members:
            if str(member.id) not in G.USR.keys():
                G.USR[str(member.id)] = mun.DefaultMunch(0)
            G.USR[str(member.id)].name = member.name
        tools.save_users()

    # Check if we need to spawn a titan.
    async def generate_titan():
        await client.wait_until_ready()
        while True:
            now = time.time()
            to_hour = G.OPT.titanhours * 3600 - (now % 3600)
            logger.info("I checked when to spawn titans.")
            logger.info(f"I'll check when to spawn titans again in {to_hour / 60} minutes.")

            for id, guild in G.GLD.items():
                if guild.titan_status is not True:
                    G.updateLOC(G.GLOC[G.GLD[str(id)].language])
                    level = idle.spawn_titan(id)
                    titan = idle.Titan(level)
                    channel = client.get_channel(guild.notification_channel)
                    if guild.notification_channel != 0:
                        await channel.send(G.LOC.msg.generated_titan.format(
                            level, tools.fn(titan.hp), round((1 - titan.armor) * 100, 2)
                        ))
            await asyncio.sleep(to_hour)

    client.loop.create_task(generate_titan())
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
