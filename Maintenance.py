import discord
import Settings as settings
import os
import configparser

# coding=utf-8

client = discord.Client()
path = "{}/".format(os.path.dirname(__file__))
if path == "/":
    path = ""
spamdict = {}
config = configparser.ConfigParser()
config.read("{}settings.ini".format(path))

print("Käynnistetään huoltokoodi...")


@client.event
async def on_ready():
    print("Tämä on huoltokatkotiedosto! Muista vaihtaa takaisin oikeaan päivityksen jälkeen.")
    await client.change_presence(game=discord.Game(name="Updating..."))


@client.event
async def on_message(message):
    msg = message.content.lower()
    viesti = client.send_message(message.channel, "Päivitys käynnissä. Katko kestää jonkin aikaa.")
    viesti_en = client.send_message(message.channel, "Bot is being updated. This usually takes only a few minutes.")
    andis_server_id = "261644024958418954"

    if message.author != client.user:
        try:
            if str(message.server.id) == andis_server_id:
                user_lang = "english"
            else:
                raise AttributeError
        except AttributeError:
            try:
                user_lang = config.get("LANGUAGE", str(message.author.id))
            except configparser.NoOptionError:
                config.set("LANGUAGE", str(message.author.id), "finnish")
                with open("{}settings.ini".format(path), "w") as configfile:
                    config.write(configfile)
                user_lang = config.get("LANGUAGE", str(message.author.id))
        if msg.startswith("!") or msg.startswith("%") or msg.startswith("&"):
            if msg != "!" and msg != "%" and msg != "&":
                if user_lang == "finnish":
                    await viesti
                else:
                    await viesti_en


if __name__ == "__main__":
    token = settings.get_credential("tokens", "maintenance")
    client.run(token)
