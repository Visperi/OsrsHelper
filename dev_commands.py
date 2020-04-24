"""
MIT License

Copyright (c) 2018-2020 Visperi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import Komennot_en as commands
import json
import discord


async def get_item_id(message, keywords, client):
    """
    Dev command to easily get the name and id of an item
    """
    itemname = " ".join(keywords)
    item_info = commands.get_iteminfo(itemname)
    if not item_info:
        await client.send_message(message.channel, "Haullasi ei löytynyt yhtään itemiä.")
        return
    await client.send_message(message.channel, f"Item name: `{item_info[0]}`\nId: `{item_info[1]}`")


async def add_puzzle(message, hakusanat, client):
    file = "Data files/Anagrams.json"
    hakusanat = " ".join(hakusanat).replace(", ", ",").split(",")
    try:
        anagram = hakusanat[0].lower()
        puzzle = hakusanat[1].lower()
    except IndexError:
        await client.send_message(message.channel, "Erottele anagrammi ja puzzlen nimi pilkulla.")
        return
    with open(file) as data_file:
        data = json.load(data_file)
    puzzle_link = await commands.hae_puzzle(message, [puzzle], client, no_message=True)
    if not puzzle_link:
        return
    else:
        try:
            data[anagram]["puzzle"] = puzzle_link
            with open(file, "w") as data_file:
                json.dump(data, data_file, indent=4)
            await client.send_message(message.channel, "Tallennustiedot:\nPuzzle: {}\nAnagram: {}"
                                      .format(puzzle.capitalize(), anagram.capitalize()))
        except KeyError:
            await client.send_message(message.channel, "Hakemaasi anagrammia ei ole tallennettu.")


async def add_object(message, hakusanat, client):
    file = "Data files/Tradeables.json"
    hakusanat = " ".join(hakusanat).replace(", ", ",").split(",")
    idlist = []
    try:
        itemname = hakusanat[0].capitalize()
        item_id = int(hakusanat[1])
    except IndexError:
        await client.send_message(message.channel, "Erottele itemin nimi ja id pilkulla. Anna ensin nimi ja sitten id.")
        return
    except ValueError:
        await  client.send_message(message.channel, "Virheellinen id.")
        return
    with open(file) as data_file:
        data = json.load(data_file)
    for itemdict in list(data.values()):
        idlist.append(itemdict["id"])
    if itemname in list(data):
        await client.send_message(message.channel, "Item on jo listalla.")
        return
    elif item_id in idlist:
        await client.send_message(message.channel, "Id on jo käytössä jollain toisella itemillä.")
        return
    else:
        data[itemname] = {"id": item_id, "high_alch": ""}
        with open(file, "w") as data_file:
            json.dump(data, data_file, indent=4)
        viesti = discord.Embed(title="Objekti lisätty", description="Itemname: {}\nItem id: {}".format(itemname,
                                                                                                       item_id))
        await client.send_message(message.channel, embed=viesti)


async def delete_object(message, hakusanat, client):
    file = "Data files/Tradeables.json"
    itemname = " ".join(hakusanat).capitalize()
    with open(file) as data_file:
        data = json.load(data_file)
    try:
        item_id = data[itemname]["id"]
        data.pop(itemname.capitalize())
    except KeyError:
        await client.send_message(message.channel, "Antamaasi tavaraa ei ole listalla.")
        return
    with open(file, "w") as data_file:
        json.dump(data, data_file, indent=4)
    viesti = discord.Embed(title="Objekti poistettu", description="Itemname: {}\nItem id: {}".format(itemname,
                                                                                                      item_id))
    await client.send_message(message.channel, embed=viesti)


async def dev_commands(message, client):
    sysadmin_commands = ["§id", "§addpuzzle", "§addobject", "§delobject", "§times used", "§addalch", "§addstream",
                         "§delstream", "§addlim", "§dellim", "§addobjects", "§check", "§get"]
    viesti = discord.Embed(title="Developer commands", description="\n".join(sysadmin_commands))\
        .set_footer(text="These commands are only for the developer's use")
    await client.send_message(message.channel, embed=viesti)


async def get_times_used(message, client):
    from operator import itemgetter
    from tabulate import tabulate
    commands_list = []

    with open("Data files/Times_used.json") as data_file:
        data = json.load(data_file)
    dates = "{} - {}".format(data["date_start"], data["date_now"])
    data.pop("date_start"), data.pop("date_now")
    all_uses = sum(list(data.values()))
    data_sorted = sorted(data.items(), key=itemgetter(1), reverse=True)
    for command in data_sorted:
        uses = command[1]
        uses_percentage = (uses / all_uses) * 100
        rpercentage = round(uses_percentage, 1)
        if rpercentage == 0.0 and uses_percentage > 0:
            rpercentage = "< 0.1"
        commands_list.append([f"{command[0]}: {command[1]}", f"[{rpercentage}%]"])
    table = "{}\n\n{}\n\nTotal: {}".format(dates, tabulate(commands_list, tablefmt="plain"), all_uses)
    await client.send_message(message.channel, f"```{table}```")


async def add_halch(message, keywords, client):
    keywords = " ".join(keywords).split(", ")
    item_info = commands.get_iteminfo(keywords[0], default_names=True)
    try:
        itemname, itemid = item_info[0], item_info[1]
    except TypeError:
        await client.send_message(message.channel, "Anna sekä itemin nimi että high alch arvo, pilkulla eroteltuna.")
        return
    if not itemname:
        await client.send_message(message.channel, "Haullasi ei löytynyt yhtään itemiä.")
        return
    with open("Data files/Tradeables.json") as data_file:
        data = json.load(data_file)
    old_value = data[itemname]["high_alch"]
    if old_value == "":
        old_value = "None"
    new_value = str(keywords[1]).replace(" ", "")
    try:
        data[itemname]["high_alch"] = int(new_value)
    except ValueError:
        await client.send_message(message.channel, "Anna high alch kokonaislukuna.")
        return
    with open("Data files/Tradeables.json", "w") as data_file:
        json.dump(data, data_file, indent=4)
    embed = discord.Embed(title="High alch value set", description=f"Name: {itemname}\nId: {itemid}\n"
                                                                   f"High alch: {old_value} -> {new_value}")
    await client.send_message(message.channel, embed=embed)


async def add_stream(message, keywords, client):
    streamers_file = "Data files/streamers.json"
    streamer = discord.utils.get(message.server.members, id=keywords[-1])
    try:
        stream_link = keywords[-2].replace("<", "").replace(">", "")
    except IndexError:
        await client.send_message(message.channel, "Please give a link to the stream too. Link first, then id.")
        return
    if not streamer:
        await client.send_message(message.channel, "Couldn't find any users with given id.")
        return
    streamer_id = streamer.id
    display_name = streamer.display_name
    streamer_name = f"{streamer.name}#{streamer.discriminator}"

    with open(streamers_file) as data_file:
        data = json.load(data_file)

    try:
        streamers_list = data[message.server.id]
    except KeyError:
        data[message.server.id] = {}
        streamers_list = data[message.server.id]
    if streamer_id in streamers_list:
        await client.send_message(message.channel, "This streamer already is in the streamers list.")
        return
    streamers_list[streamer_id] = {"stream_link": stream_link, "username": streamer_name}

    with open(streamers_file, "w") as data_file:
        json.dump(data, data_file, indent=4)
    await client.send_message(message.channel, f"Successfully added {display_name} to streamers list\n"
                                               f"Id: {streamer_id}\n"
                                               f"Link: <{stream_link}>")


async def remove_stream(message, keywords, client):
    streamers_file = "Data files/streamers.json"
    streamer = discord.utils.get(message.server.members, id=keywords[-1])
    if not streamer:
        await client.send_message(message.channel, "Couldn't find any users with given id.")
        return
    streamer_id, display_name = streamer.id, streamer.display_name

    with open(streamers_file) as data_file:
        data = json.load(data_file)

    try:
        streamers_list = data[message.server.id]
    except KeyError:
        await client.send_message(message.channel, "This server doesn't have any streamers in the list yet.")
        return
    try:
        streamers_list.pop(streamer_id)
    except ValueError:
        await client.send_message(message.channel, "Given user is not in the list for this server.")
        return
    if len(streamers_list) == 0:
        data.pop(message.server.id)

    with open(streamers_file, "w") as data_file:
        json.dump(data, data_file, indent=4)
    await client.send_message(message.channel, f"Successfully removed streamer {streamer_id} ({display_name}) from "
                                               f"streamers list.")


async def add_limit(message, keywords, client):
    limit_file = "Data files/Buy_limits.json"
    keywords = " ".join(keywords).replace(", ", ",").split(",")
    itemname = keywords[0].capitalize()

    try:
        amount = int(keywords[1])
    except IndexError:
        await client.send_message(message.channel, "Erota itemin nimi ja limitraja toisistaan pilkulla.")
        return
    except ValueError:
        await client.send_message(message.channel, "Limitrajassa oli merkkejä joiden takia siitä ei voitu muuttaa "
                                                   "luvuksi. Älä anna mitään muuta kuin itemin nimi ja sen limit.")
        return

    with open(limit_file) as data_file:
        data = json.load(data_file)
    if itemname in data:
        await client.send_message(message.channel, f"Itemille on jo asetettu limit ({data[itemname]} kpl).")
        return
    else:
        data[itemname] = str(amount)
        with open(limit_file, "w") as data_file:
            json.dump(data, data_file, indent=4)
        await client.send_message(message.channel, f"Lisättiin limit {itemname}: {str(amount)} kpl.")


async def delete_limit(message, keywords, client):
    limit_file = "Data files/Buy_limits.json"
    itemname = " ".join(keywords).capitalize()

    with open(limit_file) as data_file:
        data = json.load(data_file)
    try:
        data.pop(itemname)
    except KeyError:
        await client.send_message(message.channel, "Itemiä ei löytynyt listalta. Älä anna viestissäsi mitään muuta "
                                                   "kuin itemin nimi.")
        return
    with open(limit_file, "w") as data_file:
        json.dump(data, data_file, indent=4)
    await client.send_message(message.channel, f"Poistettiin listalta ostoraja itemille {itemname}.")


async def add_objects(message, itemlist, client):
    added_items = 0
    itemlist = itemlist.replace("§addobjects ", "")
    with open("Data files/Tradeables.json") as data_file:
        data = json.load(data_file)

    itemlist = json.loads(itemlist)
    new_items = ""
    for item in itemlist:
        item = item.split(", ")
        itemname = item[0].capitalize()
        if itemname in data:
            continue
        data[itemname] = {"high_alch": "", "id": int(item[1])}
        new_items += f"Name: {itemname}, Id: {item[1]}\n"
        added_items += 1

    if added_items == 0:
        await client.send_message(message.channel, "All the items are already in Tradeables.json.")
        return

    with open("Data files/Tradeables.json", "w") as data_file:
        json.dump(data, data_file, indent=4)
    msg = f"Added {added_items} new items to Tradeables.json:\n\n{new_items}"
    if len(msg) >= 2000:
        msg = f"Added {added_items} new items to Tradeables.json but the total length of them would be over 2000 and " \
              f"thus can't be expressed here."
    await client.send_message(message.channel, msg)


async def check_new_items(message, client):
    import requests
    if len(message.attachments) == 0:
        await client.send_message(message.channel, "Please send the `names.json` too.")
        return
    else:
        filename = message.attachments[0]["filename"]
        fileurl = message.attachments[0]["url"]
        if filename.lower() == "names.json":
            # noinspection PyBroadException
            try:
                itemdict = json.loads(requests.get(fileurl).text)
            except Exception:
                import traceback
                traceback_ = traceback.format_exc()
                await client.send_message(message.channel, f"```py\n{traceback_}```")
                return

            with open("Data files/Tradeables.json") as tradeables_file:
                tradeables = json.load(tradeables_file)

            new_items = []
            for id_ in itemdict:
                itemname = itemdict[id_]["name"]
                if itemname not in tradeables:
                    tradeables[itemname] = {"high_alch": "", "id": int(id_)}
                    new_items.append(f"{itemname}, {id_}")
            if len(new_items) == 0:
                await client.send_message(message.channel, "No new items to add.")
                return
            else:
                with open("Data files/Tradeables.json", "w") as tradeables_file:
                    json.dump(tradeables, tradeables_file, indent=4)
                new_items_joined = "\n".join(new_items)
                if len(new_items_joined) > 2000:
                    await client.send_message(message.channel, f"Added {len(new_items)} new items. Their total length "
                                                               f"was over 2000 characters.")
                else:
                    await client.send_message(message.channel, f"Added {len(new_items)} new items:\n\n"
                                                               f"{new_items_joined}")


async def get_file(message, keywords, client):
    filename = " ".join(keywords)
    filepath = path + filename
    try:
        await client.send_file(message.channel, filepath)
    except FileNotFoundError:
        await client.send_message(message.channel, "File not found.")
        return
    except discord.errors.Forbidden:
        await client.send_message(message.channel, "My role doesn't have permission to send files.")
        return


async def manage_drinks(message, keywords, client):
    try:
        server_id = message.server.id
    except AttributeError:
        await client.send_message(message.channel, "This command doesn't support direct messages.")
        return

    action = keywords[0]
    target_user_id = keywords[1]
    try:
        member_obj = message.server.get_member(target_user_id)
        target_display_name = member_obj.display_name
    except AttributeError:
        target_display_name = target_user_id

    if action == "reset" and len(keywords) != 2:
        await client.send_message(message.channel, f"Invalid amount of parameters. Got {len(keywords)} but expected 2.")
        return
    elif len(keywords) != 3 and action != "reset":
        await client.send_message(message.channel, f"Invalid amount of parameters. Got {len(keywords)} but expected 3.")
        return

    with open("Data files/drinks.json", "r") as drinks_file:
        drinks_data = json.load(drinks_file)

    try:
        server_drinks = drinks_data[server_id]
    except KeyError:
        await client.send_message(message.channel, "This server doesn't have any drinks yet.")
        return
    if action == "reset":
        del server_drinks[target_user_id]
        if len(server_drinks) == 0:
            del drinks_data[server_id]
        success_str = f"Succesfully reset drinks for {target_display_name}."
    else:
        try:
            amount = int(keywords[2])
        except ValueError:
            await client.send_message(message.channel, "Third parameter was not convertible to an integer.")
            return
        try:
            target_user_drinks = server_drinks[target_user_id]
        except KeyError:
            await client.send_message(message.channel, "Target doesn't have any drinks yet.")
            return

        if action == "remove":
            target_user_drinks -= amount
        elif action == "add":
            target_user_drinks += amount
        elif action == "set":
            target_user_drinks = amount
        else:
            await client.send_message(message.channel, "Unknown operation.")
            return

        server_drinks[target_user_id] = target_user_drinks
        success_str = f"Succesfully modified drinks for {target_display_name}. They now have " \
                      f"{target_user_drinks} drinks."

    with open("Data files/drinks.json", "w") as output_file:
        json.dump(drinks_data, output_file, indent=4)

    await client.send_message(message.channel, success_str)

if __name__ == '__main__':
    print("Please run the Main.py to use any commands. They work only through Discord.")
    exit()
