import asyncio
import collections
import os

import discord
import youtube_dl
from discord.ext import commands

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
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
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

    @commands.command(name="join", description="Joins user's or a given voice channel")
    async def _join(self, ctx, *, channel: discord.VoiceChannel = None):
        if not channel:
            if not ctx.author.voice:
                return await ctx.send(f"User: {ctx.author} must be in a voice channel or a channel name must be given")
            channel = ctx.author.voice.channel

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        return await channel.connect()

    @commands.command(name="play", description="Streams audio from a given youtube url",  aliases=("stream", "yt"))
    async def _play(self, ctx, url):
        async with ctx.typing():
            player = await self.YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            if not ctx.voice_client.is_playing():
                ctx.voice_client.play(player, after=lambda e: self._play_queue(ctx))
                return await ctx.send(f"Now playing: {player.title}")
            else:
                self.song_queue.append(player)
                return await ctx.send(f"Queuing {player.title}")

    @commands.command(name="queue", description="Lists songs in the queue", aliases=("list", "songs"))
    async def _queue(self, ctx):
        return await ctx.send(
            "```Queue:\n\t" +
            '\n\t'.join([f"{i+1}. {p.title}" for i, p in enumerate(list(self.song_queue))]) + "```")

    def _play_queue(self, ctx):
        if len(self.song_queue) > 0:
            ctx.voice_client.play(self.song_queue.pop(), after=lambda e: self._play_queue(ctx))

    # @commands.command(name="clip", description="Plays audio from a downloaded clip, give no argument to list the clips")
    # async def _clip(self, ctx, query=None):
    #     clips = [f for f in os.listdir('./audio_clips') if f.endswith(('.m4a', '.mp3', '.webm'))]

    #     if not query:
    #         return await ctx.send(
    #             "```Available clips:\n\t" +
    #             '\n\t'.join([f"{i+1}. {f}" for i, f in enumerate(clips)]) + "```")

    #     # Choose query
    #     for clip in clips:
    #         if clip.lower().startswith(query.lower()):
    #             query = './audio_clips/' + clip
    #             break

    #     source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
    #     ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)

    #     await ctx.send(f"Now playing: {query.split('/')[-1]}")

    # @commands.command(name="download", description="Downloads given youtube url and names the file")
    # async def _download(self, ctx, url, *name):
    #     name = ' '.join(name)
    #     dl_options = youtube_dl.YoutubeDL({
    #         'format': 'bestaudio/best',
    #         'outtmpl': f'./audio_clips/{name}.%(ext)s',
    #         'restrictfilenames': True,
    #         'noplaylist': True,
    #         'nocheckcertificate': True,
    #         'ignoreerrors': False,
    #         'logtostderr': False,
    #         'quiet': True,
    #         'no_warnings': True,
    #         'default_search': 'auto',
    #         'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
    #         })

    #     async with ctx.typing():
    #         player = await self.YTDLSource.from_url(url, loop=self.bot.loop, stream=False, options=dl_options)

    #     await ctx.send(f'Now downloading: {player.title} as {player.title}')

    @commands.command(name="stop", description="Disconnects bot from voice channel")
    async def _stop(self, ctx):
        await ctx.voice_client.disconnect()

    @commands.command(name="skip", description="Disconnects bot from voice channel")
    async def _skip(self, ctx):
        async with ctx.typing():
            ctx.voice_client.stop()
            await ctx.send(f"Skipping...\nNow playing {self.song_queue[0].title}")
            self._play_queue(ctx)
        return

    @commands.command(name="volume", description="Changes the volume of the player")
    async def volume(self, ctx, volume: int):
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Changed volume to {volume}%")

    @_play.before_invoke
    @_clip.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
