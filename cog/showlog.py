import discord
import itertools
from discord.ext import commands
from utils import parsing
from utils import checks

config = parsing.parse_json('config.json')["logging"]


class ShowLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(checks.is_owner)
    async def showlog(self, ctx, num_lines=10):
        """
        Display the last couple lines of the log [ADMIN ONLY]
        """
        with open(config["file"], "r") as f:
            text = f.readlines()
        length = len(text)
        if num_lines < 1:
            num_lines = 5
        if num_lines > length:
            num_lines = length
        send = "```"
        for line in itertools.islice(text, length - num_lines, length):
            send += line
        send += "```"
        await ctx.send(send)


def setup(bot):
    bot.add_cog(ShowLog(bot))
