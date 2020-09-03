import asyncio

import discord
from discord.ext import commands

import youtube_dl

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


    class YTDLSource(discord.PCMVolumeTransformer):
        def __init__(self, source, *, data, volume=0.5):
            super().__init__(source, volume)

            self.data = data

            self.title = data.get('title')
            self.url = data.get('url')

        @classmethod
        async def from_url(cls, url, *, loop=None, stream=False):
            ytdl = youtube_dl.YoutubeDL({
                'format': 'bestaudio/best',
                'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
                'restrictfilenames': True,
                'noplaylist': True,
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'logtostderr': False,
                'quiet': True,
                'no_warnings': True,
                'default_search': 'auto',
                'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
            })

            ffmpeg_options = {'options': '-vn'}

            loop = loop or asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

            if 'entries' in data:
                # take first item from a playlist
                data = data['entries'][0]

            filename = data['url'] if stream else ytdl.prepare_filename(data)
            return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


    @commands.command(name="join", description = "Joins user's or a given voice channel")
    async def _join(self, ctx, *, channel: discord.VoiceChannel=None):
        if not channel:
            if not ctx.author.voice:
                return await ctx.send("User: {} must be in a voice channel or a channel name must be given".format(ctx.author))
            channel = ctx.author.voice.channel

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        return await channel.connect()


    @commands.command(name="play", description = "Streams audio from a given youtube url",  aliases = ("stream", "yt"))
    async def _play(self, ctx, *, url):
        async with ctx.typing():
            player = await self.YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send('Now playing: {}'.format(player.title))


    @commands.command(name = "stop", description = "Disconnects bot from voice channel")
    async def stop(self, ctx):
        await ctx.voice_client.disconnect()


    @commands.command(name = "volume", description = "Changes the volume of the player")
    async def volume(self, ctx, volume: int):
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send("Changed volume to {}%".format(volume))


    @_play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


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
