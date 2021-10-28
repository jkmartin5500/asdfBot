import datetime

from discord.ext import commands

import chessdotcom

class Chess(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        chessdotcom.Client.aio = True
        self.gamemodes = {"blitz": "chess_blitz", "rapid": "chess_rapid", "bullet": "chess_bullet", "daily": "chess_daily"}

    @commands.command(name="chessinfo", description="Gets player info on chess.com from given username")
    async def _info(self, ctx, *args):
        try:
            player, mode = args
            response = await chessdotcom.client.get_player_stats(player)
            stats = response.json['stats'][self.gamemodes[mode]]
            message = f"Player: {player} | Mode: {mode}\n"
            current = stats['last']['rating']
            current_date = datetime.date.fromtimestamp(stats['last']['date'])
            best = stats['best']['rating']
            best_date = datetime.date.fromtimestamp(stats['best']['date'])
            message += f"Current Rating: {current} as of {current_date}\nBest Rating: {best} as of {best_date}"

            return await ctx.send("```" + message + "```")

        except ValueError:
            return await ctx.send("Usage is !chessinfo {username} {mode}")
