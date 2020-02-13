import globals as G
import tools
import munch


class Item:
    """Container class for information about items, as read in the idle.json file (inside "items")

    It just unpacks the dictionary as an object.
    """
    def __init__(self, key):
        self.__dict__ = G.IDLE["items"][key]
        self.id = key
        self.name = G.LOC["items"][key].name


class Inventory:
    """Handles retrieving and generating all items in a player's inventory."""
    def __init__(self, user_id):
        """Find and make all items for a certain user.

        Every time we access a user's items we should do it through this class.

        Args:
            user_id: str
                Id of user to make items for.
        """
        self.user_id = user_id
        if G.USR[user_id].inventory in [0, None]:
            # We never made any items for this user.
            tools.update_user(user_id=user_id, stat="inventory", set=munch.Munch())

        if len(G.USR[user_id].inventory) == 0:
            self.is_empty = True
        else:
            self.is_empty = False

        self.content = []
        for key, is_owned in G.USR[user_id].inventory.items():
            if is_owned:
                self.content.append(Item(key))

    def update_content(self):
        """Forces to reload contents of inventory for the user."""
        self.content = []
        for key, is_owned in G.USR[self.user_id].inventory.items():
            if is_owned:
                self.content.append(Item(key))

    def add_item(self, key):
        G.USR[self.user_id].inventory[key] = True
        tools.save_users()
        self.update_content()

    def remove_item(self, key):
        G.USR[self.user_id].inventory[key] = False
        tools.save_users()
        self.update_content()


# Buy an item with Tokens ----------------------------------------------------------------------
def buy_item_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.buy.id):
        return True
    return False


def buy_item_logic(message):
    """Handles buying an item and generates a string to push to chat."""
    user_id = str(message.author.id)
    inventory = Inventory(user_id)
    arg = str(message.content[len(G.OPT.prefix) + len(G.LOC.commands.buy.id) + 1:])
    arg = arg.lower()
    out = tools.MsgBuilder()

    for key, item in G.LOC["items"].items():
        # Search for the item in the localization file.
        if arg == item.name.lower():
            identifier = key
            new_item = Item(identifier)
            break
    else:
        out.add(G.LOC.commands.buy.unknown)
        return out.parse()

    for item in inventory.content:
        # Cannot buy an already-owned item.
        if item.id == identifier:
            out.add(G.LOC.commands.buy.already_bought.format(arg))
            return out.parse()

    if G.IDLE["items"][identifier].builds_from is not None:
        # Cannot buy if we don't have the required items.
        current_ids = [item.id for item in inventory.content]
        required_items = set(G.IDLE["items"][identifier].builds_from)
        if required_items.issubset(current_ids) is False:
            out.add(G.LOC.commands.buy.no_requirements)
            return out.parse()
    else:
        required_items = set()

    if len(inventory.content) >= (G.IDLE.max_items - len(required_items)):
        # Cannot buy an item if inventory is full
        out.add(G.LOC.commands.buy.nospace.format(G.IDLE.max_items))
        return out.parse()

    if G.USR[user_id].tokens <= new_item.cost:
        # Cannot buy if we don't have enough tokens
        out.add(G.LOC.commands.buy.not_enough.format(
            tools.fn(G.USR[user_id].tokens),
            tools.fn(new_item.cost)
        ))
        return out.parse()

    # If we get here, all requirements to buy the item are fulfilled
    tools.update_user(user_id=user_id, stat="tokens", increase=-new_item.cost)
    inventory.add_item(new_item.id)

    if G.IDLE["items"][identifier].builds_from is not None:
        # Remove required items
        for item in inventory.content:
            if item.id in G.IDLE["items"][identifier].builds_from:
                inventory.remove_item(item.id)

    inventory.update_content()  # Probably useless

    out.add(G.LOC.commands.buy.success.format(
        new_item.name,
        tools.fn(new_item.cost)
    ))
    return out.parse()


# Sell items---------------------------------------------------------------------------
def sell_item_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.sell.id):
        return True
    return False


def sell_item_logic(message):
    # Grab from message the name and id of the item
    user_id = str(message.author.id)
    inventory = Inventory(user_id)
    arg = str(message.content[len(G.OPT.prefix) + len(G.LOC.commands.sell.id) + 1:])
    arg = arg.lower()
    out = tools.MsgBuilder()

    for key, item in G.LOC["items"].items():
        # Search for the item in the localization file.
        if arg == item.name.lower():
            identifier = key
            new_item = Item(identifier)
            break
    else:
        out.add(G.LOC.commands.sell.unknown)
        return out.parse()

    if identifier not in [x.id for x in inventory.content]:
        out.add(G.LOC.commands.sell.noitem.format(new_item.name))
        return out.parse()

    # Remove the item
    inventory.remove_item(identifier)
    # Refund tokens
    tools.update_user(user_id, "tokens", increase=new_item.resell)

    out.add(G.LOC.commands.sell.success.format(new_item.name, tools.fn(new_item.resell)))
    return out.parse()


# Show shop with available items ------------------------------------------------------
def show_shop_perm(message):
    if message.content.startswith(G.OPT.prefix + G.LOC.commands.shop.id):
        return True
    return False


def show_shop_logic(message):
    """Show the item shop

    Should automatically grab new items as they are in the localization files.
    """
    out = tools.MsgBuilder()
    out.add(G.LOC.commands.shop.intro)

    for identifier, item in G.LOC["items"].items():
        out.add(G.LOC.commands.shop.item_template.format(
            item.name,
            item.info,
            G.IDLE["items"][identifier].cost
        ))
    return out.parse()


def make_commands():
    """Makes all commands relative to this module"""
    tools.add_command(logic=buy_item_logic, permission=buy_item_perm)
    tools.add_command(logic=show_shop_logic, permission=show_shop_perm, where="user")
    tools.add_command(logic=sell_item_logic, permission=sell_item_perm)
