import io
from nextcord.ext import commands
from nextcord import Member, User
from nextcord.ext.commands import Context
from nextcord import File
from ssbu_amiibo import SsbuAmiiboDump as AmiiboDump
from amiibo import AmiiboMasterKey
import json
import copy


with open('assets/key_retail.bin', 'rb') as keys:
    master_keys = AmiiboMasterKey.from_combined_bin(keys.read())

class StorageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.dm_only()
    @commands.command()
    async def store(self, ctx: Context):
        dump = AmiiboDump(master_keys, await ctx.message.attachments[0].read())
        dump.unlock()
        with open('amiibo.json', "r") as _json:
            amiibo = json.load(_json)
            name: str = copy.deepcopy(dump.amiibo_nickname)
            dump.lock()
            namenum = 1
            if str(ctx.author.id) not in amiibo['users']:
                amiibo['users'][str(ctx.author.id)] = {}
                amiibo['users'][str(ctx.author.id)]['amiibo'] = {}
            while name in amiibo['users'][str(ctx.author.id)]['amiibo']:
                    namenum += 1
                    if '-v' not in name:
                        name = name + "-v"
                    if name[-1] == 'v':
                        name += str(namenum)
                    if str(namenum) != list(name)[-1]:
                        name = list(name)
                        name[-1] = namenum
                        name = str(name).replace("'", '').strip('[').strip(']').replace(',', '').replace(' ', '')
            amiibo['users'][str(ctx.author.id)]['amiibo'][f"{name}"] = [dump.data.hex()]
        with open('amiibo.json', "w") as _json:
            json.dump(amiibo, _json, indent=4)
        await ctx.send(f'Stored {name}!')

    @commands.dm_only()
    @commands.command()
    async def list(self, ctx: Context):
        with open('amiibo.json', "r") as _json:
            amiibo = json.load(_json)
        output = "The amiibo you have stored are: ```\n"
        for amiibo in amiibo['users'][str(ctx.author.id)]['amiibo']:
            output += f'{amiibo}\n'
        output +='```'
        await ctx.send(output)

    @commands.dm_only()
    @commands.command()
    async def get(self, ctx: Context, name: str):
        with open('amiibo.json', "r") as _json:
            amiibo = json.load(_json)
        vb = File(io.BytesIO(bytes.fromhex(amiibo['users'][str(ctx.author.id)]['amiibo'][name][0])), name + '.bin')
        await ctx.send(file=vb)

    @commands.dm_only()
    @commands.command()
    async def send(self, ctx: Context, user: Member, name: str):
        with open('amiibo.json', "r") as _json:
            amiibo = json.load(_json)
        vb = File(io.BytesIO(bytes.fromhex(amiibo['users'][str(ctx.author.id)]['amiibo'][name][0])), name + '.bin')
        await user.send(file=vb)

    @commands.dm_only()
    @commands.command()
    async def delete(self, ctx: Context, name):
        with open('amiibo.json', "r") as _json:
            amiibo = json.load(_json)
        del amiibo['user'][str(ctx.author.id)]['amiibo'][name]
        with open('amiibo.json', "w+") as _json:
            amiibo = json.dump(amiibo, _json)

def setup(bot):
    bot.add_cog(StorageCog(bot))

