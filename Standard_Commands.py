import random

from discord.ext import commands


class Standard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roll", description="Rolls dice in NdN format")
    async def _roll(self, ctx, arg: str):
        try:
            rolls, limit = map(int, arg.split('d'))
        except ValueError:
            return await ctx.send("Format has to be in NdN!")

        result = [random.randint(1, limit) for _ in range(rolls)]
        await ctx.send(', '.join(str(i) for i in result) + "\tSum: " + str(sum(result)))

    @commands.command(name="choose", description="Chooses from a group of choices")
    async def _choose(self, ctx, *args):
        await ctx.send("I choose " + random.choice(' '.join([arg for arg in args if arg not in {'or', 'and', ' '}])))

    @commands.command(name="team", description="Picks teams from 5 people given in order best to worst")
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
