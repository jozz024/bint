import io

import bin_modify_utils
import nextcord
from nextcord import File
from nextcord.ext import commands
from nextcord.ext.commands import Context


class BinCog(commands.Cog):

    @commands.dm_only()
    @commands.command(name = 'transplant')
    async def transplant(self, ctx: Context, *, character):
        transplant = bin_modify_utils.Transplant()
        try:
            try:
                bin = transplant.transplant(character, await ctx.message.attachments[0].read())
            except IndexError:
                await ctx.send('Please attach a file.')
            await ctx.send(file=File(io.BytesIO(bin), filename = ctx.message.attachments[0].filename))
        except KeyError:
            await ctx.send('Invalid Character Name.')

    @commands.dm_only()
    @commands.command(name='shufflesn')
    async def shuffle_sn(self, ctx: Context):
        shuffle = bin_modify_utils.BinUtils()
        try:
            dump = shuffle.open_dump(await ctx.message.attachments[0].read())
            dump.unlock()
            dump.uid_hex = shuffle.shuffle_sn()
            dump.lock()
            await ctx.send(file=File(io.BytesIO(dump.data), filename = ctx.message.attachments[0].filename))
        except IndexError:
            await ctx.send('Please attach a file.')

    @commands.dm_only()
    @commands.command(name='rename')
    async def rename(self, ctx: Context, new_name):
        rename = bin_modify_utils.BinUtils()
        try:
            bin = rename.rename(new_name, await ctx.message.attachments[0].read())
            await ctx.send(file=File(io.BytesIO(bin), filename = ctx.message.attachments[0].filename))
        except IndexError:
            await ctx.send('Please attach a file.')

    @commands.dm_only()
    @commands.command(name = 'setspirits')
    async def setspirits(self, ctx: Context, attack: int, defense: int, skill_1 = 'none', skill_2 = 'none', skill_3 = 'none'):
        setspirits = bin_modify_utils.Spirits()
        try:
            try:
                bin = setspirits.set_spirits(await ctx.message.attachments[0].read(), attack, defense, skill_1, skill_2, skill_3)
            except KeyError:
                await ctx.send('Invalid Spirit Skills.')
            await ctx.send(file=File(io.BytesIO(bin), filename = ctx.message.attachments[0].filename))
        except IndexError:
            await ctx.send('Please attach a file.')

    @commands.dm_only()
    @commands.command(nane = 'bin2ryu')
    async def bin2ryu(self, ctx: Context):
        ryujinx = bin_modify_utils.Ryujinx()
        try:
            bin = ryujinx.bin_to_json(await ctx.message.attachments[0].read())
            await ctx.send(file=File(io.BytesIO(bin.encode('utf-8')), filename = ctx.message.attachments[0].filename.replace('.bin', '.json')))
        except IndexError:
            await ctx.send('Please attach a file.')

    @commands.dm_only()
    @commands.command(nane = 'ryu2bin')
    async def ryu2bin(self, ctx: Context):
        ryujinx = bin_modify_utils.Ryujinx()
        try:
            bin = ryujinx.json_to_bin(await ctx.message.attachments[0].read())
            await ctx.send(file=File(io.BytesIO(bin), filename = ctx.message.attachments[0].filename.replace('.json', '.bin')))
        except IndexError:
            await ctx.send('Please attach a file.')

    @commands.dm_only()
    @commands.command(name='bineval')
    async def bineval(self, ctx: Context):
        eval = bin_modify_utils.Evaluate()
        try:
            output = eval.bineval(await ctx.message.attachments[0].read())
            if len(output) <= 2000:
                await ctx.send(output)
            else:
                lines = output.splitlines()
                line_num = 0
                output = ""
                for line in lines:
                    output += line + "\n"
                    line_num += 1

                    if line_num == 24:
                        await ctx.send(output + "```")
                        output = "```"
                await ctx.send(output)
        except IndexError:
            await ctx.send('Please attach a file.')

    @commands.dm_only()
    @commands.command(name = 'convert')
    async def convert(self, ctx: Context):
        nfctools = bin_modify_utils.NFCTools()
        try:
            bin = nfctools.txt_to_bin(await ctx.message.attachments[0].read())
            await ctx.send(file=File(io.BytesIO(bin), filename = ctx.message.attachments[0].filename.replace('.txt', '.bin')))
        except IndexError:
            await ctx.send('Please attach a file.')

def setup(bot):
    bot.add_cog(BinCog(bot))

