import discord
from discord.ext import commands

import random, json


with open('config.json', 'r') as config:
    TOKEN = json.loads(config.read())['token']

description = ''' An all purpose discord bot for everyday use '''
client = commands.Bot(command_prefix=commands.when_mentioned_or("!"), description = description)

class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping", description = "pong")
    async def _ping(self, ctx):
        await ctx.send("pong")

    @commands.command(name="roll", description = "Rolls dice in NdN format")
    async def _roll(self, ctx, arg: str):
        try:
            rolls, limit = map(int, arg.split('d'))
        except Exception:
            await ctx.send("Format has to be in NdN!")
            return

        result = [random.randint(1, limit) for r in range(rolls)]
        await ctx.send(', '.join(str(i) for i in result) + "\tSum: " + str(sum(result)))

    @commands.command(name="choose", description = "Chooses from a group of choices")
    async def _choose(self, ctx, *args):
        await ctx.send("I choose " + random.choice(' '.join([arg for arg in args if arg not in {'or', 'and'}])))

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="join", description = "Joins user's or a given voice channel")
    async def _join(self, ctx, *, channel: discord.VoiceChannel=None):
        if not channel:
            if not ctx.author.voice:
                return await ctx.send("User: {} must be in a voice channel or a channel name must be given".format(ctx.author))
            channel = ctx.author.voice.channel

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        return await channel.connect()

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name='!'))
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

if __name__ == "__main__":
    client.add_cog(Basic(client))
    client.add_cog(Music(client))
    client.run(TOKEN)
