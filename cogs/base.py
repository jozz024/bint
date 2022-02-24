from nextcord.ext.commands import Context
from nextcord.ext import commands
import os
import sys
import re
import asyncio
import traceback

class BaseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.async_call_shell = self.async_call_shell

    def restart_bot(self): 
        os.execv(sys.executable, ['py'] + sys.argv)

    async def async_call_shell(
        self, shell_command: str, inc_stdout=True, inc_stderr=True
    ):
        pipe = asyncio.subprocess.PIPE
        proc = await asyncio.create_subprocess_shell(
            str(shell_command), stdout=pipe, stderr=pipe
        )

        if not (inc_stdout or inc_stderr):
            return "??? you set both stdout and stderr to False????"

        proc_result = await proc.communicate()
        stdout_str = proc_result[0].decode("utf-8").strip()
        stderr_str = proc_result[1].decode("utf-8").strip()

        if inc_stdout and not inc_stderr:
            return stdout_str
        elif inc_stderr and not inc_stdout:
            return stderr_str

        if stdout_str and stderr_str:
            return f"stdout:\n\n{stdout_str}\n\n" f"======\n\nstderr:\n\n{stderr_str}"
        elif stdout_str:
            return f"stdout:\n\n{stdout_str}"
        elif stderr_str:
            return f"stderr:\n\n{stderr_str}"

        return "No output."

    @commands.is_owner()
    @commands.command(name = 'restart')
    async def restart(self, ctx):
        self.restart_bot()

    @commands.is_owner()
    @commands.command()
    async def pull(self, ctx: Context, auto=False):
        """Does a git pull, bot manager only."""
        tmp = await ctx.send("Pulling...")
        git_output = await self.bot.async_call_shell("git pull")
        await tmp.edit(content=f"Pull complete. Output: ```{git_output}```")
        if auto:
            cogs_to_reload = re.findall(r"cogs/([a-z_]*).py[ ]*\|", git_output)
            for cog in cogs_to_reload:
                cog_name = "cogs." + cog
                try:
                    self.bot.unload_extension(cog_name)
                    self.bot.load_extension(cog_name)
                    await ctx.send(f":white_check_mark: `{cog}` successfully reloaded.")
                except:
                    await ctx.send(
                        f":x: Cog reloading failed, traceback: "
                        f"```\n{traceback.format_exc()}\n```"
                    )
                    return


def setup(bot):
    bot.add_cog(BaseCog(bot))