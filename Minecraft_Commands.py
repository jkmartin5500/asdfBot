from discord.ext import commands
import boto3

class Minecraft(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.lambda_client = boto3.client('lambda', region_name='us-east-2')

    @commands.command(name="server", aliases=("minecraft", "mc"), description="Starts the minecraft server")
    async def _start_server(self, ctx):
        await self.lambda_client.invoke(FunctionName='mc_start', InvocationType='Event')
