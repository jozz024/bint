from nextcord.ext import commands
import nextcord
from nextcord import File
import os

STORAGE_DIR = "./amiibo/"


class storageCog(commands.Cog):
    @commands.command(name="storagehelp")
    async def help_cmd(self, ctx):
        retmsg = (
            "`!store <amiibo nickname>` (and attach the bin)\n"
            "`!listbins`\n"
            "`!renamestoredbin <old amiibo nickname>, <new amiibo nickname>`\n"
            "`!delete <amiibo nickname>`\n"
            # "`!send <Tag the host> <amiibo nickname>`\n"
            "`!download <amiibonickname>`"
        )
        await ctx.send(retmsg)

    @commands.command(name="listbins")
    async def list_cmd(self, ctx):
        filelist = os.listdir(STORAGE_DIR)
        amiibolist = [x for x in filelist if x.startswith(str(ctx.author.id))]
        namelist = ["-".join(x.split("-")[1:]).replace(".bin", "") for x in amiibolist]
        print(namelist)
        retmsg = "The amiibo you have stored are:\n" + "\n".join(namelist)
        await ctx.send(retmsg)

    @commands.command(name="delete")
    @commands.dm_only()
    async def delete_cmd(self, ctx, to_del):
        try:
            filename = STORAGE_DIR + str(ctx.author.id) + "-" + to_del + ".bin"
            os.remove(filename)
            await ctx.send(f"Successfully deleted {to_del}")
        except Exception as exc:
            logging.warning(exc)
            await ctx.send("Deletion Failed")

    @commands.command(name="renamestoredbin")
    @commands.dm_only()
    async def rename_cmd(self, ctx, oldname, newname):
        try:
            oldfilename = STORAGE_DIR + str(ctx.author.id) + "-" + oldname + ".bin"
            newfilename = STORAGE_DIR + str(ctx.author.id) + "-" + newname + ".bin"
            os.rename(oldfilename, newfilename)
            await ctx.send("Successfully renamed {} to {}".format(oldname, newname))
        except Exception as exc:
            if "No such file or directory" in str(exc):
                await ctx.send(
                    "File does not exist, make sure your spelling is correct"
                )
            elif "not enough values to unpack" in str(exc):
                await ctx.send("Not enough names provided, should be comma separated")
            elif "too many values to unpack" in str(exc):
                await ctx.send("Too many names provided, calm down")
            else:
                await ctx.send("Failed to rename")

    @commands.command(name="store")
    @commands.dm_only()
    async def store_cmd(self, ctx, nick):
        BINSIZES = [532, 540, 572]
        if ctx.message.attachments[0].size in BINSIZES and ctx.message.attachments[
            0
        ].filename.endswith("bin"):
            try:
                filepathname = STORAGE_DIR + str(ctx.author.id) + "-" + nick + ".bin"
                await ctx.message.attachments[0].save(fp=filepathname)
                await ctx.send("Successfully stored - " + nick)
            except Exception as exc:
                logging.warning(exc)
                await ctx.send("Failed to Store")
        else:
            await ctx.send("Improper bin size")

    @commands.command(name="send")
    async def send(self, ctx, userid, to_send):
        try:
            user = ctx.message.mentions[0]
            print(user)
            filename = STORAGE_DIR + str(ctx.author.id) + "-" + to_send + ".bin"
            sendname = STORAGE_DIR + to_send + ".bin"
            os.rename(filename, sendname)
            await user.send(file=File(sendname))
            os.rename(sendname, filename)
            await ctx.send(
                "Successfully sent {} to {}".format(to_send, str(user)),
            )
        except Exception as exc:
            print(exc)
            if "Cannot send messages to this user" in str(exc):
                await ctx.send(
                    "Cannot send messages to this user, they may have DMs turned off"
                )
            elif "No such file or directory" in str(exc):
                await ctx.send(
                    "File does not exist, make sure your spelling is correct"
                )
            else:
                await ctx.send("Failed to Send")

    @commands.command(name="download")
    @commands.dm_only()
    async def dl(self, ctx, amiiname):
        try:
            filename = STORAGE_DIR + str(ctx.author.id) + "-" + amiiname + ".bin"
            sendname = STORAGE_DIR + amiiname + ".bin"
            os.rename(filename, sendname)
            await ctx.send(file=File(sendname))
            os.rename(sendname, filename)
        except Exception as exc:
            logging.warning(exc)
            if "No such file or directory" in str(exc):
                await ctx.send(
                    "File does not exist, make sure your spelling is correct"
                )
            else:
                await ctx.send("Failed to Download")


def setup(bot):
    bot.add_cog(storageCog(bot))
