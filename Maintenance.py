"""
MIT License

Copyright (c) 2022 Visperi

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

import discord
import Settings as settings

# coding=utf-8

client = discord.Client()

print("Starting maintenance module...")


@client.event
async def on_ready():
    print("This is a maintenance file and doesn't have any commands! Remember to change back to Main.py!")
    await client.change_presence(game=discord.Game(name="Updating..."))


@client.event
async def on_message(message):
    content = message.content

    if content.startswith("!") or content.startswith("%") or content.startswith("&"):
        await client.send_message(message.channel, "The bot is being updated. This shouldn't take too long.")


if __name__ == "__main__":
    token = settings.get_credential("tokens", "maintenance")
    client.run(token)
