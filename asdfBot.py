import json

import discord
from discord.ext import commands

import Music_Commands
import Standard_Commands

with open('config.json', 'r') as config:
    TOKEN = json.loads(config.read())['token']

description = ''' An all purpose discord bot for everyday use '''
client = commands.Bot(command_prefix=commands.when_mentioned_or("!"), description=description)


class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping", description="pong")
    async def _ping(self, ctx):
        await ctx.send("pong")


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name='!'))
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


if __name__ == "__main__":
    client.add_cog(Main(client))
    client.add_cog(Standard_Commands.Standard(client))
    client.add_cog(Music_Commands.Music(client))
    client.run(TOKEN)
