from nextcord.ext import commands
import nextcord
from dictionaries import *
import requests
from character_dictionary import CharacterDictionary
from amiibo_functions import BinManager
from amiibo import AmiiboMasterKey
from ssbu_amiibo import SsbuAmiiboDump as AmiiboDump
from nextcord import File

default_assets_location = r"Brain_Transplant_Assets"
characters_location = r"Brain_Transplant_Assets/characters.xml"
char_dict = CharacterDictionary(characters_location)
binmanagerinit = BinManager(char_dict)


class binCog(commands.Cog):
    @commands.command(name="convert")
    @commands.dm_only()
    async def convert_nfc_tools_file_to_bin(self, ctx):
        export_string_lines = None
        hex = ""
        print(str(self, ctx.message.attachments[0].filename))
        print(str(self, ctx.message.attachments[0].url))
        await ctx.message.attachments[0].save(fp="txt files/nextcord.txt")
        with open("txt files/nextcord.txt") as file:
            export_string_lines = file.readlines()

        for line in export_string_lines:
            match = re.search(r"(?:[A-Fa-f0-9]{2}:){3}[A-Fa-f0-9]{2}", line)
            if match:
                hex = hex + match.group(0).replace(":", "")

        bin = bytes.fromhex(hex)
        with open(
            f"bin files/{str(self, ctx.message.attachments[0].filename).strip('.txt')}.bin",
            mode="wb",
        ) as new_file:
            new_file.write(bin)
        await ctx.send(
            file=File(
                f"bin files/{str(self, ctx.message.attachments[0].filename).strip('.txt')}.bin"
            )
        )

    @commands.command(name="transplant")
    @commands.dm_only()
    async def brain_transplant(self, ctx, *, character):
        try:
            character = character
            await ctx.message.attachments[0].save(
                fp=f"old bins/{ctx.message.attachments[0].filename}"
            )
            binmanagerinit.transplant(
                bin_location=f"old bins/{ctx.message.attachments[0].filename}",
                character=character.title(),
                saveAs_location=f"new bins/{ctx.message.attachments[0].filename}",
                randomize_SN=True,
            )
            await ctx.send(file=File(f"new bins/{ctx.message.attachments[0].filename}"))
        except KeyError:
            try:
                character = TRANSLATION_TABLE_CHARACTER_TRANSPLANT[
                    character.replace(" ", "")
                ]
                await ctx.message.attachments[0].save(
                    fp=f"old bins/{ctx.message.attachments[0].filename}"
                )
                binmanagerinit.transplant(
                    bin_location=f"old bins/{ctx.message.attachments[0].filename}",
                    character=character.title(),
                    saveAs_location=f"new bins/{ctx.message.attachments[0].filename}",
                    randomize_SN=True,
                )
                await ctx.send(
                    file=File(f"new bins/{ctx.message.attachments[0].filename}")
                )
            except KeyError:
                await ctx.send(f"'{character}' is an invalid character.")

    @commands.command(name="shuffleSN".lower())
    @commands.dm_only()
    async def shufflenfpsn(self, ctx):
        await ctx.message.attachments[0].save(
            fp=f"old bins/{ctx.message.attachments[0].filename}"
        )
        binmanagerinit.randomize_sn(
            bin_location=f"old bins/{ctx.message.attachments[0].filename}"
        )
        await ctx.send(file=File(f"old bins/{ctx.message.attachments[0].filename}"))

    @commands.command(name="setspirits")
    @commands.dm_only()
    async def spiritedit(
        self, ctx, attack, defense, ability1="none", ability2="none", ability3="none"
    ):
        await ctx.message.attachments[0].save(
            fp=f"old bins/{ctx.message.attachments[0].filename}"
        )
        print(ability1)
        print(ability2)
        print(ability3)
        try:
            binmanagerinit.setspirits(
                f"old bins/{ctx.message.attachments[0].filename}",
                attack,
                defense,
                ability1,
                ability2,
                ability3,
                f"new bins/{ctx.message.attachments[0].filename}",
            )
            await ctx.send(
                f"{attack}, {defense}",
                file=File(f"new bins/{ctx.message.attachments[0].filename}"),
            )
        except IndexError:
            await ctx.send("Illegal Setup")

    @commands.command(name="rename")
    @commands.dm_only()
    async def rename(self, ctx, *, newamiiboname):
        await ctx.message.attachments[0].save(
            fp=f"old bins/{ctx.message.attachments[0].filename}"
        )
        with open(r"/".join([default_assets_location, "key_retail.bin"]), "rb") as fp_j:
            master_keys = AmiiboMasterKey.from_combined_bin(fp_j.read())
        with open(f"old bins/{ctx.message.attachments[0].filename}", "rb") as fp:
            dump = AmiiboDump(master_keys, fp.read())
        dump.unlock()
        dump.amiibo_nickname = newamiiboname
        dump.lock()
        with open(f"new bins/{ctx.message.attachments[0].filename}", "wb") as fp:
            fp.write(dump.data)
        await ctx.send(file=File(f"new bins/{ctx.message.attachments[0].filename}"))

    @commands.command(name="decrypt")
    @commands.is_owner()
    async def decrypt(self, ctx):
        await ctx.message.attachments[0].save(
            fp=f"old bins/{ctx.message.attachments[0].filename}"
        )
        binmanagerinit.decrypt(
            f"old bins/{ctx.message.attachments[0].filename}",
            f"new bins/{ctx.message.attachments[0].filename}",
        )
        await ctx.send(file=File(f"new bins/{ctx.message.attachments[0].filename}"))

    @commands.command(name="binedit")
    @commands.is_owner()
    async def binedit(self, ctx, aggression, edgeguard, anticipation, defensiveness):
        await ctx.message.attachments[0].save(
            fp=f"old bins/{ctx.message.attachments[0].filename}"
        )
        binmanagerinit.personalityedit(
            f"old bins/{ctx.message.attachments[0].filename}",
            aggression,
            edgeguard,
            anticipation,
            defensiveness,
            f"new bins/{ctx.message.attachments[0].filename}",
        )
        await ctx.send(file=File(f"new bins/{ctx.message.attachments[0].filename}"))


def setup(bot):
    bot.add_cog(binCog(bot))
