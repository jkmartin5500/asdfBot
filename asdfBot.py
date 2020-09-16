import asyncio

import discord
from discord.ext import commands

import youtube_dl

import random, json, os, collections


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
            return await ctx.send("Format has to be in NdN!")

        result = [random.randint(1, limit) for r in range(rolls)]
        await ctx.send(', '.join(str(i) for i in result) + "\tSum: " + str(sum(result)))


    @commands.command(name="choose", description = "Chooses from a group of choices")
    async def _choose(self, ctx, *args):
        await ctx.send("I choose " + random.choice(' '.join([arg for arg in args if arg not in {'or', 'and', ' '}])))


    @commands.command(name="team", description = "Picks teams from 5 people given in order best to worst")
    async def _team(self, ctx, *args):
        if len(args) % 2 == 0:
            teams = list(args)
            # Two best stay separate
            # Next two best shuffle
            teams[2:4] = random.sample(teams[2:4], len(teams[2:4]))
            # Middle Players random
            teams[4:8] = random.sample(teams[4:8], len(teams[4:8]))
            # Worst two stay separate
            teams[8:10] = random.sample(teams[8:10], len(teams[8:10]))

            return await ctx.send('\n'.join(["Team 1:"] + teams[0:len(teams):2] + ["Team 2:"] + teams[1:len(teams):2]))
        await ctx.send("Teams uneven")



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


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = collections.deque()


    class YTDLSource(discord.PCMVolumeTransformer):
        def __init__(self, source, *, data, volume=0.5):
            super().__init__(source, volume)

            self.data = data

            self.title = data.get('title')
            self.url = data.get('url')


        @classmethod
        async def from_url(cls, url, *, loop=None, stream=False, options=ytdl):
            loop = loop or asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: options.extract_info(url, download=not stream))

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
    async def _play(self, ctx, url):
        async with ctx.typing():
            player = await self.YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            if not ctx.voice_client.is_playing():
                ctx.voice_client.play(player, after=lambda e: self._play_queue(ctx))
                return await ctx.send("Now playing: {}".format(player.title))
            else:
                self.song_queue.append(player)
                return await ctx.send("Queuing {}".format(player.title))


    @commands.command(name="queue", description= "Lists songs in the queue", aliases= ("list", "songs"))
    async def _queue(self, ctx):
        return await ctx.send("```Queue:\n\t" + '\n\t'.join(["{}. {}".format(i+1, p.title) for i, p in enumerate(list(self.song_queue))]) + "```")


    def _play_queue(self, ctx):
        if len(self.song_queue) > 0:
            ctx.voice_client.play(self.song_queue.pop(), after=lambda e: self._play_queue(ctx))


    @commands.command(name="clip", description = "Plays audio from a downloaded clip, give no argument to list the clips")
    async def _clip(self, ctx, query=None):
        clips = [f for f in os.listdir('./audio_clips') if f.endswith(('.m4a', '.mp3', '.webm'))]

        if not query:
            return await ctx.send("```Available clips:\n\t" + '\n\t'.join(["{}. {}".format(i+1, f) for i, f in enumerate(clips)]) + "```")

        # Choose query
        for clip in clips:
            if clip.lower().startswith(query.lower()):
                query = './audio_clips/' + clip
                break

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
        ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send('Now playing: {}'.format(query.split('/')[-1]))


    @commands.command(name="download", description = "Downloads given youtube url and names the file")
    async def _download(self, ctx, url, *name):
        name = ' '.join(name)
        dl_options = youtube_dl.YoutubeDL({
            'format': 'bestaudio/best',
            'outtmpl': './audio_clips/{}.%(ext)s'.format(name),
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

        async with ctx.typing():
            player = await self.YTDLSource.from_url(url, loop=self.bot.loop, stream=False, options=dl_options)

        await ctx.send('Now downloading: {} as {}'.format(player.title, player.title))


    @commands.command(name = "stop", description = "Disconnects bot from voice channel")
    async def _stop(self, ctx):
        await ctx.voice_client.disconnect()


    @commands.command(name = "skip", description = "Disconnects bot from voice channel")
    async def _skip(self, ctx):
        async with ctx.typing():
            ctx.voice_client.stop()
            await ctx.send("Skipping...\nNow playing {}".format(self.song_queue[0].title))
            self._play_queue(ctx)
        return


    @commands.command(name = "volume", description = "Changes the volume of the player")
    async def volume(self, ctx, volume: int):
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send("Changed volume to {}%".format(volume))


    @_play.before_invoke
    @_clip.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")


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
