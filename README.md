This is a massive work in project thing that is probably horribly written, barely works and will give nightmares to anyone who can actually code properly. Read the source code at your own peril.

This is a discord bot made for my personal discord channel. It doesn't do much; it mostly insults whomever uses it. I run it on my Raspberry pi 3.

Current Features:

- Very few actual features;
- Can roll dice;
- Automatically generates text for the Help command from localization files;
- Has a help command;
- Can customize prefix from config file;
- Stores user data that should be kept between reboots in "users.json" file; This should probably be empty on the first boot;
- "Greets" users on landing in the channel;
- Supports both IT and EN localizations. Hopefully.

Current not-features-that-I-want-to-be-features:

- Some kind of features. Any of them;
- Some form of documentations for the aforementioned features;
- Interactive idle game that can be played on Discord itself.

Current ideas:

- League of legends statistics? I would need to know how to use their API though.
- World News?
- Something AI-driven? Like a channel for a chat with the bot itself? I don't think it can be run on a pi though.
- Something that can handle music streaming? Thing is it looks real difficult coding-wise.

---

It uses the following libraries:

- discord.py (Duh)
- munch (I like using the dot style to access my dictionaries)

If anyone actually finds this and wants to contribute, please do. I need help. Really, please. Fix my ugly ass code. Teach me senpai. You can contact me, whenever. Or you can open a ticket saying how bad this is, I don't care!
