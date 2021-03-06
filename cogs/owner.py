"""
Dredd, discord bot
Copyright (C) 2020 Moksej
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.
You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import discord
import math
import humanize
import aiohttp
import typing
import os
import importlib
import asyncio
import discordlists
import config
import json

from discord import Webhook, AsyncWebhookAdapter
from discord.ext import commands
from discord.utils import escape_markdown
from utils import default, btime
from utils.paginator import Pages, TextPages
from prettytable import PrettyTable
from db import emotes
from datetime import datetime
from utils.default import color_picker

class owner(commands.Cog, name="Owner"):

    def __init__(self, bot):
        self.bot = bot
        self.help_icon = "<:owners:691667205082841229>"
        self.big_icon = "https://cdn.discordapp.com/emojis/691667205082841229.png?v=1"
        self._last_result = None
        self.api = discordlists.Client(self.bot)  # Create a Client instance
        self.api.set_auth("discordextremelist.xyz", config.DEL_TOKEN)
        self.api.set_auth("discord.bots.gg",  config.DBGG_TOKEN)
        self.api.set_auth("discord.boats",  config.DBoats_TOKEN)
        self.api.set_auth("glennbotlist.xyz",  config.GLENN_TOKEN)
        self.api.set_auth("mythicalbots.xyz",  config.MYTH_TOKEN)
        self.api.set_auth("botsfordiscord.com", config.BFD_TOKEN)
        self.api.set_auth("botlist.space", config.BOTSPACE_TOKEN)
        self.api.set_auth("discordbots.co", config.DISCORD_BOTS_TOKEN)
        self.api.start_loop()
        self.color = color_picker('colors')

    async def cog_check(self, ctx: commands.Context):
        """
        Local check, makes all commands in this cog owner-only
        """
        if not await ctx.bot.is_owner(ctx.author):

            if ctx.guild.id == 671078170874740756:
                try:
                    await ctx.message.add_reaction('<:youtried:731954681739345921>')
                except:
                    pass
            await ctx.send(f"{emotes.bot_owner} | This command is owner-locked", delete_after=20)
            return False
        return True

    @commands.group(brief="Main commands")
    async def dev(self, ctx):
        """ Developer commands.
        Used to manage bot stuff."""

        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

# ! Users
    
    @dev.command()
    async def userlist(self, ctx):
        """ Whole list of users that bot can see """

        try:
            await ctx.message.delete()
        except:
            pass
        async with ctx.channel.typing():
            await asyncio.sleep(2)
        user_list = []
        for user in self.bot.users:
            user_list.append(user)

        user_lists = []  # Let's list the users
        for num, user in enumerate(user_list, start=0):
            user_lists.append(f'`[{num + 1}]` **{user.name}** ({user.id})\n**Created at:** {btime.human_timedelta(user.created_at)}\n**────────────────────────**\n')

        paginator = Pages(ctx,
                          title=f"__Users:__ `[{len(user_lists)}]`",
                          entries=user_lists,
                          per_page = 10,
                          embed_color=self.color['embed_color'],
                          show_entry_count=False,
                          author=ctx.author)

        await paginator.paginate()

    @dev.command()
    async def nicks(self, ctx, user: discord.User, limit: int = None):
        """ View someone nicknames """
        nicks = []
        for num, nick in enumerate(await self.bot.db.fetch("SELECT * FROM nicknames WHERE user_id = $1 LIMIT $2", user.id, limit), start=0):
            nicks.append(f"`[{num + 1}]` {nick['nickname']}\n")
        
        if not nicks:
            return await ctx.send(f"{emotes.red_mark} **{user}** has had no nicknames yet.")

        paginator = Pages(ctx,
                          title=f"{user} [{user.id}]",
                          entries=nicks,
                          per_page = 10,
                          embed_color=self.color['embed_color'],
                          show_entry_count=False,
                          author=ctx.author)

        await paginator.paginate()

    @dev.command(brief='Clear user nicknames')
    async def clearnicks(self, ctx, user: discord.User, guild: int = None):
        """ Clear user nicknames """

        db_check = await self.bot.db.fetch("SELECT * FROM nicknames WHERE user_id = $1", user.id)

        if db_check is None:
            return await ctx.send(f"{user} has had no nicknames yet")
        
        if len(db_check) == 0:
            return await ctx.send(f"{user} has no nicknames in his history.")

        try:
            if guild is None:
                def check(r, u):
                    return u.id == ctx.author.id and r.message.id == checkmsg.id
                checkmsg = await ctx.send(f"Are you sure you want to clear all **{len(db_check)}** **{user}** nicknames?")
                await checkmsg.add_reaction(f'{emotes.white_mark}')
                await checkmsg.add_reaction(f'{emotes.red_mark}')
                react, users = await self.bot.wait_for('reaction_add', check=check, timeout=30)
                
                if str(react) == f"{emotes.white_mark}":
                    await checkmsg.delete()
                    await self.bot.db.execute("DELETE FROM nicknames WHERE user_id = $1", user.id)
                    return await ctx.send(f"{emotes.white_mark} {len(db_check)} nickname(s) were removed from {user}'s history", delete_after=15)
                
                if str(react) == f"{emotes.red_mark}":
                    await checkmsg.delete()
                    return await ctx.send(f"Not clearing any nicknames.", delete_after=15)
                
            if guild is not None:
                def check(r, u):
                    return u.id == ctx.author.id and r.message.id == checkmsg.id
                db_checks = await self.bot.db.fetch("SELECT * FROM nicknames WHERE user_id = $1 and guild_id = $2", user.id, guild)
                    
                g = self.bot.get_guild(guild)
                checkmsg = await ctx.send(f"Are you sure you want to clear all **{len(db_checks)}** {user} nicknames in **{g}** server?")
                await checkmsg.add_reaction(f'{emotes.white_mark}')
                await checkmsg.add_reaction(f'{emotes.red_mark}')
                react, users = await self.bot.wait_for('reaction_add', check=check, timeout=30)
                
                if str(react) == f"{emotes.white_mark}":
                    await checkmsg.delete()
                    await self.bot.db.execute("DELETE FROM nicknames WHERE user_id = $1 AND guild_id = $2", user.id, guild)
                    return await ctx.send(f"{emotes.white_mark} {len(db_checks)} nickname(s) were removed from {user}'s history in {g} guild.", delete_after=15)
                
                if str(react) == f"{emotes.red_mark}":
                    await checkmsg.delete()
                    return await ctx.send("Not removing any nicknames.", delete_after=15)
        
        except asyncio.TimeoutError:
            try:
                await checkmsg.clear_reactions()
                return await checkmsg.edit(content=f"Cancelling..")
            except:
                return
    
# ! SQL

    @dev.command(name="sql")
    async def sql(self, ctx, *, query):
        try:
            if not query.lower().startswith("select"):
                data = await self.bot.db.execute(query)
                return await ctx.send(data)

            data = await self.bot.db.fetch(query)
            if not data:
                return await ctx.send("Not sure what's wrong in here.")
            columns = []
            values = []
            for k in data[0].keys():
                columns.append(k)

            for y in data:
                rows = []
                for v in y.values():
                    rows.append(v)
                values.append(rows)

            x = PrettyTable(columns)
            for d in values:
                x.add_row(d)
            
            pages = TextPages(ctx,
                          text=f'\n{x}')
            return await pages.paginate()
        except Exception as e:
            await ctx.send(e)


# ! Blacklist

    @dev.command(brief="Blacklist a guild", aliases=['guildban'])
    async def guildblock(self, ctx, guild: int, *, reason: str):
        """ Blacklist bot from specific guild """

        try:
            await ctx.message.delete()
        except:
            pass

        db_check = await self.bot.db.fetchval("SELECT guild_id FROM blockedguilds WHERE guild_id = $1", guild)

        if await self.bot.db.fetchval("SELECT _id FROM noblack WHERE _id = $1", guild):
            return await ctx.send("You cannot blacklist that guild")

        if db_check is not None:
            return await ctx.send("This guild is already in my blacklist.")

        await self.bot.db.execute("INSERT INTO blockedguilds(guild_id, reason, dev) VALUES ($1, $2, $3)", guild, reason, ctx.author.id)
        self.bot.blacklisted_guilds[guild] = [reason]
        server = self.bot.support

        g = self.bot.get_guild(guild)
        await ctx.send(f"I've successfully added **{g}** guild to my blacklist", delete_after=10)
        try:
            try:
                owner = g.owner
                e = discord.Embed(color=self.color['deny_color'], description=f"Hello!\nYour server **{ctx.guild}** has been blacklisted by {ctx.author}.\n**Reason:** {reason}\n\nIf you wish to appeal feel free to join the [support server]({self.bot.support})", timestamp=datetime.utcnow())
                e.set_author(name=f"Blacklist state updated!", icon_url=self.bot.user.avatar_url)
                await owner.send(embed=e)
            except Exception as e:
                print(e)
                await ctx.send("Wasn't able to message guild owner")
                pass
            await g.leave()
            await ctx.send(f"I've successfully left `{g}`")
        except Exception:
            pass

    @dev.command(brief="Unblacklist a guild", aliases=['guildunban'])
    async def guildunblock(self, ctx, guild: int):
        """ Unblacklist bot from blacklisted guild """

        try:
            await ctx.message.delete()
        except:
            pass

        db_check = await self.bot.db.fetchval("SELECT guild_id FROM blockedguilds WHERE guild_id = $1", guild)

        if db_check is None:
            return await ctx.send("This guild isn't in my blacklist.")

        await self.bot.db.execute("DELETE FROM blockedguilds WHERE guild_id = $1", guild)
        self.bot.blacklisted_guilds.pop(guild)

        bu = await self.bot.db.fetch("SELECT * FROM blockedguilds")

        g = self.bot.get_guild(guild)
        await ctx.send(f"I've successfully removed **{g}** ({guild}) guild from my blacklist")

    @dev.command(brief="Bot block user", aliases=['botban'])
    async def botblock(self, ctx, user: discord.User, *, reason: str = None):
        """ Blacklist someone from bot commands """
        try:
            await ctx.message.delete()
        except:
            pass

        if reason is None:
            reason = 'No reason'

        with open('db/badges.json', 'r') as f:
            data = json.load(f)

        db_check = await self.bot.db.fetchval("SELECT user_id FROM blacklist WHERE user_id = $1", user.id)

        if user.id == 345457928972533773 or user.id == 373863656607318018:
            return await ctx.send("You cannot blacklist that user")


        if db_check is not None:
            return await ctx.send("This user is already in my blacklist.")

        try:
            data['Users'][f'{user.id}']["Badges"] = [f'{emotes.blacklisted}']
            self.bot.user_badges[f"{user.id}"]["Badges"] = [f'{emotes.blacklisted}']
        except KeyError:
            data['Users'][f'{user.id}'] = {"Badges": [f'{emotes.blacklisted}']}
            self.bot.user_badges[f"{user.id}"] = {"Badges": [f'{emotes.blacklisted}']}

        g = self.bot.get_guild(671078170874740756)
        member = g.get_member(user.id)
        if member:
            for role in member.roles:
                try:
                    await member.remove_roles(role, reason='User was blacklisted')
                except:
                    pass
        
            role = member.guild.get_role(734537587116736597)
            bot_admin = member.guild.get_role(674929900674875413)
            await member.add_roles(role, reason='User is blacklisted')
            overwrites = {
                member.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                member.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                bot_admin: discord.PermissionOverwrite(read_messages=True, send_messages=False)
            }
            category = member.guild.get_channel(734539183703588954)
            channel = await member.guild.create_text_channel(name=f'{member.id}-blacklist', overwrites=overwrites, category=category, reason=f"User was blacklisted")
            await channel.send(f"{member.mention} Hello! Since you're blacklisted, I'll be locking your access to all the channels. If you wish to appeal, feel free to do so in here. Leaving the server will get you banned immediately.\n\n**Blacklist reason:** {''.join(reason)}", allowed_mentions=discord.AllowedMentions(users=True))
        
        with open('db/badges.json', 'w') as f:
            data = json.dump(data, f, indent=4)

        await self.bot.db.execute("INSERT INTO blacklist(user_id, reason, dev) VALUES ($1, $2, $3)", user.id, reason, ctx.author.id)
        self.bot.blacklisted_users[user.id] = [reason]

        try:
            e = discord.Embed(color=self.color['deny_color'], description=f"Hello!\nYou've been blacklisted from using Dredd commands by {ctx.author}.\n**Reason:** {reason}\n\nIf you think your blacklist was unfair, please join the [support server]({self.bot.support})", timestamp=datetime.utcnow())
            e.set_author(name=f"Blacklist state updated!", icon_url=self.bot.user.avatar_url)
            await user.send(embed=e)
        except Exception as e:
            await ctx.channel.send(f"{emotes.warning} **Error occured:** {e}")
            pass
        await ctx.send(f"I've successfully added **{user}** to my blacklist", delete_after=10)


    @dev.command(brief="Bot unblock user", aliases=['botunban'])
    async def botunblock(self, ctx, user: discord.User, *, reason: str):
        """ Unblacklist someone from bot commands """

        try:
            await ctx.message.delete()
        except:
            pass

        db_check = await self.bot.db.fetchval("SELECT user_id FROM blacklist WHERE user_id = $1", user.id)

        with open('db/badges.json', 'r') as f:
            data = json.load(f)

        if db_check is None:
            return await ctx.send("This user isn't in my blacklist.")

        await self.bot.db.execute("DELETE FROM blacklist WHERE user_id = $1", user.id)
        self.bot.blacklisted_users.pop(user.id)
        try:
            data['Users'].pop(f"{user.id}")
            self.bot.user_badges.pop(f"{user.id}")
        except KeyError:
            pass
        
        g = self.bot.get_guild(671078170874740756)
        member = g.get_member(user.id)

        if member:
            try:
                if emotes.bot_early_supporter not in data['Users'][f'{member.id}']['Badges']:
                    data['Users'][f"{member.id}"]['Badges'] += [emotes.bot_early_supporter]
                    self.bot.user_badges[f"{user.id}"]["Badges"] += [f'{emotes.bot_early_supporter}']
                else:
                    return
            except KeyError:
                data['Users'][f"{member.id}"] = {"Badges": [emotes.bot_early_supporter]}
                self.bot.user_badges[f"{user.id}"] = {"Badges": [emotes.bot_early_supporter]}

            role1 = member.guild.get_role(741749103280783380)
            role2 = member.guild.get_role(741748979917652050)
            role3 = member.guild.get_role(741748857888571502)
            role4 = member.guild.get_role(674930044082192397)
            role5 = member.guild.get_role(679642623107137549)
            await member.add_roles(role1, role2, role3, role4, role5)
            await member.remove_roles(discord.Object(id=734537587116736597))
            for channel in member.guild.get_channel(734539183703588954).channels:
                if channel.name == f'{member.id}-blacklist':
                    await channel.delete()
        
        with open('db/badges.json', 'w') as f:
            data = json.dump(data, f, indent=4)
        
        try:
            e = discord.Embed(color=self.color['approve_color'], description=f"Hello!\nYou've been un-blacklisted from using Dredd commands by {ctx.author}.\n**Reason:** {reason}", timestamp=datetime.utcnow())
            e.set_author(name=f"Blacklist state updated!", icon_url=self.bot.user.avatar_url)
            await user.send(embed=e)
        except Exception as e:
            await ctx.channel.send(f"{emotes.warning} **Error occured:** {e}")
            pass

        await ctx.send(f"I've successfully removed **{user}** from my blacklist", delete_after=10)
    
    @dev.command(brief='DM block a user', aliases=['dmban'])
    async def dmblock(self, ctx, user: discord.User):

        try:
            await ctx.message.delete()
        except:
            pass

        db_check = await self.bot.db.fetchval("SELECT user_id FROM dm_black WHERE user_id = $1", user.id)


        if db_check is not None:
            return await ctx.send("This user is already in my dm blacklist.")

        await self.bot.db.execute("INSERT INTO dm_black(user_id) values($1)", user.id)

        await ctx.send(f"I've successfully added **{user}** to my dm blacklist", delete_after=10)
    
    @dev.command(aliases=["bu"])
    async def blacklistedusers(self, ctx, page: int = 1):

        try:
            await ctx.message.delete()
        except:
            pass

        user_list = []
        for num, res, in enumerate(await self.bot.db.fetch("SELECT * FROM blacklist"), start=0):
            if res['time']:
                time = btime.human_timedelta(res['time'])
            else:
                time = 'Unknwon'
            user_list.append(f"`[{num + 1}]`\n**User:** {await self.bot.fetch_user(res['user_id'])} ({res['user_id']})\n**Reason:** {res['reason']}\n**Issued:** {time}\n**Issued by:** {await self.bot.fetch_user(res['dev'])} ({res['dev']})\n")

        if not user_list:
            return await ctx.send(f"There are no blacklisted users!")

        paginator = Pages(ctx,
                          title=f"Blacklisted users:",
                          entries=user_list,
                          per_page = 5,
                          embed_color=self.color['embed_color'],
                          show_entry_count=False,
                          author=ctx.author)

        await paginator.paginate()

# ! Bot managment

    @dev.command(brief="Change updates")
    async def update(self, ctx, *, updates: str):
        """ Change current updates """
        try:
            await ctx.message.delete()
        except:
            pass

        db_check = await self.bot.db.fetchval(f"SELECT * FROM updates")

        if db_check is None:
            await self.bot.db.execute("INSERT INTO updates(update) VALUES ($1)", updates)
            embed = discord.Embed(color=self.color['embed_color'],
                                  description=f"Set latest updates to {updates}")
            await ctx.send(embed=embed, delete_after=10)

        if db_check is not None:
            await self.bot.db.execute(f"UPDATE updates SET update = $1", updates)
            embed = discord.Embed(color=self.color['embed_color'],
                                  description=f"Set latest updates to {updates}")
            await ctx.send(embed=embed, delete_after=10)


    
    @dev.command(brief='Change log of bot')
    async def changes(self, ctx):

        try:
            await ctx.message.delete()
        except:
            pass

        e = discord.Embed(color=self.color['logging_color'])
        e.set_author(icon_url=self.bot.user.avatar_url, name=f'Change log for V{self.bot.version}')
        e.description = self.bot.most_recent_change
        e.set_footer(text=f"© {self.bot.user}")

        await ctx.send(embed=e)

    @dev.command(brief='Add guild to whitelist')
    async def addwhite(self, ctx, guild: int):
        check = await self.bot.db.fetchval("SELECT * FROM noblack WHERE _id = $1", guild)

        if check:
            return await ctx.send(f"{emotes.red_mark} Already whitelisted")
        elif not check:
            await self.bot.db.execute("INSERT INTO noblack(_id) VALUES($1)", guild)
            await ctx.send(f"{emotes.white_mark} Done!")

# ! Status managment
    
    @commands.group(brief="Change status/pfp/nick", description="Change bot statuses and other.")
    @commands.is_owner()
    async def change(self, ctx):
        """Change bots statuses/avatar/nickname"""
        if ctx.invoked_subcommand is None:
            pass

    @change.command(name="playing", brief="Playing status", description="Change bot status to playing")
    @commands.is_owner()
    async def change_playing(self, ctx, *, playing: str):
        """ Change playing status. """
        await ctx.trigger_typing()
        try:
            await self.bot.change_presence(
                activity=discord.Game(type=0, name=playing),
                status=discord.Status.online
            )
            await ctx.send(f"Changed playing status to **{playing}**")
            await ctx.message.delete()
        except discord.InvalidArgument as err:
            await ctx.send(err)
        except Exception as e:
            await ctx.send(e)

    @change.command(name='listening', brief="Listening status", description="Change bot status to listening")
    @commands.is_owner()
    async def change_listening(self, ctx, *, listening: str):
        """ Change listening status. """
        await ctx.trigger_typing()
        try:
            await self.bot.change_presence(
                activity=discord.Activity(type=discord.ActivityType.listening,
                                          name=listening)
            )
            await ctx.send(f"Changed listening status to **{listening}**")
            await ctx.message.delete()
        except discord.InvalidArgument as err:
            await ctx.send(err)
        except Exception as e:
            await ctx.send(e)

    @change.command(name="watching", brief="Watching status", description="Change bot status to watching")
    @commands.is_owner()
    async def change_watching(self, ctx, *, watching: str):
        """ Change watching status. """
        await ctx.trigger_typing()
        try:
            await self.bot.change_presence(
                activity=discord.Activity(type=discord.ActivityType.watching,
                                          name=watching)
            )
            await ctx.send(f"Changed watching status to **{watching}**")
            await ctx.message.delete()
        except discord.InvalidArgument as err:
            await ctx.send(err)
        except Exception as e:
            await ctx.send(e)
            await ctx.message.delete()

    @change.command(name="nickname", aliases=['nick'], brief="Change nick", description="Change bot's nickname")
    @commands.is_owner()
    async def change_nickname(self, ctx, *, name: str = None):
        """ Change nickname. """
        await ctx.trigger_typing()
        try:
            await ctx.guild.me.edit(nick=name)
            await ctx.message.delete()
            if name:
                await ctx.send(f"Changed nickname to **{name}**")
            else:
                await ctx.send("Removed nickname")
                await ctx.message.delete()
        except Exception as err:
            await ctx.send(err)

    @change.command(name="avatar", brief="Change avatar", description="Change bot's avatar")
    @commands.is_owner()
    async def change_avatar(self, ctx, url: str = None):
        """ Change avatar. """
        if url is None and len(ctx.message.attachments) == 1:
            url = ctx.message.attachments[0].url
        else:
            url = url.strip('<>') if url else None

        try:
            async with aiohttp.ClientSession() as c:
                async with c.get(url) as f:
                    bio = await f.read()
            await self.bot.user.edit(avatar=bio)
            embed = discord.Embed(color=self.color['embed_color'],
                                  description=f"Changed the avatar!")
            embed.set_thumbnail(url=url)
            await ctx.send(embed=embed)
        except aiohttp.InvalidURL:
            await ctx.send("URL is invalid")
        except discord.InvalidArgument:
            await ctx.send("URL doesn't contain any image")
        except discord.HTTPException as err:
            await ctx.send(err)
        except TypeError:
            await ctx.send("You need to either provide an image URL or upload one with the command")

    @dev.command(aliases=['edit', 'editmsg'], category="Messages", brief="Edit msg")
    @commands.is_owner()
    async def editmessage(self, ctx, id: int, *, newmsg: str):
        """Edits a message sent by the bot"""
        try:
            msg = await ctx.channel.fetch_message(id)
        except discord.errors.NotFound:
            return await ctx.send("Couldn't find a message with an ID of `{}` in this channel".format(id))
        if msg.author != self.bot.user:
            return await ctx.send("That message was not sent by me")
        await msg.edit(content=newmsg)
        await ctx.message.delete()

# ! Guild managment 

    @commands.group(brief="Guild settings")
    @commands.is_owner()
    async def guild(self, ctx):
        """Guild related commands!"""
        if ctx.invoked_subcommand is None:
            pass

    @guild.command(brief="Get invites", description="Get all invites of guild bot's in")
    @commands.is_owner()
    async def inv(self, ctx, guild: int):
        """Get all the invites of the server."""
        try:
            guildid = self.bot.get_guild(guild)
            guildinvs = await guildid.invites()
            pager = commands.Paginator()
            for Invite in guildinvs:
                pager.add_line(Invite.url)
            for page in pager.pages:
                await ctx.send(page)
        except discord.Forbidden:
            await ctx.send(f"{emotes.warning} Was unable to fetch invites.")

    @guild.command(brief="Create inv", description="Create inv to any guild bot is in")
    async def createinv(self, ctx, channel: int):
        """ Create invite for a server (get that server channel id's first)"""
        try:
            channelid = self.bot.get_channel(channel)
            InviteURL = await channelid.create_invite(max_uses=1)
            await ctx.send(InviteURL)
        except discord.Forbidden:
            await ctx.send(f"{emotes.warning} Was unable to create an invite.")

    @guild.command(aliases=['slist', 'serverlist'], name="list", brief="Guild list", description="View all guilds bot is in")
    @commands.is_owner()
    async def _list(self, ctx, page: int = 1):
        """List the guilds I am in."""
        try:
            await ctx.message.delete()
        except:
            pass
        guild_list = []
        for num, guild in enumerate(self.bot.guilds, start=0):
            people = len([x for x in guild.members if not x.bot])
            bots = len([x for x in guild.members if x.bot])
            botfarm = int(100 / len(guild.members) * bots)
            guild_list.append(f"`[{num + 1}]` {guild} ({guild.id}) `[Ratio: {botfarm}%]`\n**Joined:** {humanize.naturaltime(guild.get_member(self.bot.user.id).joined_at)}\n")

        paginator = Pages(ctx,
                          title=f"Guilds I'm In:",
                          thumbnail=None,
                          entries=guild_list,
                          per_page = 10,
                          embed_color=self.color['embed_color'],
                          show_entry_count=False,
                          author=ctx.author)

        await paginator.paginate()

    @guild.command(name="inspect", brief="Inspect a guild")
    async def _inspect(self, ctx, guild: int):

        try:
            guild = self.bot.get_guild(guild)
            people = len([x for x in guild.members if not x.bot])
            bots = len([x for x in guild.members if x.bot])
            botfarm = int(100 / len(guild.members) * bots)
            sperms = dict(guild.me.guild_permissions)
            perm = []
            for p in sperms.keys():
                if sperms[p] == True and guild.me.guild_permissions.administrator == False:
                    perm.append(f"`{p}`, ")

            invites = ''
            try:
                guildinv = await guild.invites()
                for inv in guildinv[:1]:
                    invites += f'{inv}'
            except:
                pass

            invs = f'[Invite]({invites})' if invites else ""


            if guild.me.guild_permissions.administrator == True:
                    perm = [f'`Administrator`  ']
            e = discord.Embed(color=self.color['embed_color'], title=f'**{guild}** Inspection')
            e.set_thumbnail(url=guild.icon_url)
            if botfarm > 50 and len(guild.members) > 15:
                e.description = f"{emotes.warning} This **MIGHT** be a bot farm, do you want me to leave this guild? `[Ratio: {botfarm}%]`"
            e.add_field(name='Important information:', value=f"""
**Total Members:** {len(guild.members):,} which {people:,} of them are humans and {bots:,} bots. `[Ratio: {botfarm}%]` {invs}
**Server Owner:** {guild.owner} ({guild.owner.id})""", inline=False)
            e.add_field(name='Other information:', value=f"""
**Total channels/roles:** {len(guild.channels)} {emotes.other_unlocked} / {len(guild.roles)} roles
**Server created at:** {default.date(guild.created_at)}
**Joined server at:** {btime.human_timedelta(guild.get_member(self.bot.user.id).joined_at)} ({default.date(guild.get_member(self.bot.user.id).joined_at)})
**Prefix:** {escape_markdown(self.bot.prefixes[guild.id])}""", inline=False)
            e.add_field(name="My permissions:", value="".join(perm)[:-2])
            await ctx.send(embed=e)
        except AttributeError:
            await ctx.send(f"{emotes.warning} Can't seem to find that guild, are you sure the ID is correct?")



    @guild.command(name='leave', category="Other", brief="Leave a guild", description="Make bot leave a suspicious guild")
    @commands.is_owner()
    async def leave(self, ctx, guild: int, reason: str):
        """ Make bot leave suspicious guild """
        try:
            await ctx.message.delete()
        except:
            pass
        if guild == 667065302260908032 or guild == 684891633203806260 or guild == 650060149100249091 or guild == 368762307473571840:
            return await ctx.send("You cannot leave that guild")
        server = self.bot.support
        owner = self.bot.get_guild(guild).owner
        g = self.bot.get_guild(guild).name
        e = discord.Embed(color=self.color['logging_color'], description=f"Hello!\nI was forced to leave your server **{g}** by {ctx.author}\n**Reason:** {reason}\n\nIf you have any questions feel free to join the [support server]({server})", timestamp=datetime.utcnow())
        e.set_author(name=f"Force leave executed!", icon_url=self.bot.user.avatar_url)
        try:
            await owner.send(embed=e)
        except Exception as e:
            pass
        await self.bot.get_guild(guild).leave()

    # ! Guild update count

    @guild.command(name='count', brief="Update guild count")
    async def guild_count(self, ctx):

        channel = self.bot.get_channel(681837728320454706)
        channel2 = self.bot.get_channel(697906520863801405)

        await channel.edit(name=f"Watching {len(self.bot.guilds)} guilds")
        await channel2.edit(name=f"Watching {len(self.bot.users)} users")
        await ctx.message.add_reaction(f'{emotes.white_mark}')
    
# ! Social 

    @dev.command(brief="DM a user", description="Direct message a user. DO NOT ABUSE IT!")
    @commands.is_owner()
    async def dm(self, ctx, id: str, *, msg: str):
        """ DM an user """
        try:
            await ctx.message.delete()
        except:
            pass
        try:
            if not id.isdigit():
                return await ctx.author.send(f"{emotes.warning} ID must be integer")
            try:
                user = self.bot.dm[int(id)]
            except Exception as e:
                return await ctx.author.send(f"{emotes.warning} Error occured! {default.traceback_maker(e, advance=True)}")
            user = self.bot.get_user(user)
            await user.send(msg)
            logchannel = self.bot.get_channel(674929832596865045)
            logembed = discord.Embed(
                description=msg, color=0x81C969, timestamp=datetime.utcnow())
            logembed.set_author(name=f"I've sent a DM to {user} | #{id}", icon_url=user.avatar_url)
            logembed.set_footer(text=f"User ID: {user.id}")
            await logchannel.send(embed=logembed)

        except discord.errors.Forbidden:
            await ctx.author.send("Couldn't send message to that user. Maybe he's not in the same server with me?")


    @dev.command(brief="Announce something", description="Announce something in announcement channel")
    async def announce(self, ctx, *, message: str):
        """ Announce something in support server announcement channel """

        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(config.WEBHOOK_URL, adapter=AsyncWebhookAdapter(session))
            await webhook.send(message, username=ctx.author.name, avatar_url=ctx.author.avatar_url)
            
        await ctx.message.add_reaction(f'{emotes.white_mark}')

# ! Command managment

    @dev.command(brief="Disable enabled cmd")
    async def disablecmd(self, ctx, *, command):
        """Disable the given command. A few important main commands have been blocked from disabling for obvious reasons"""
        cmd = self.bot.get_command(command)

        if cmd is None:
            embed = discord.Embed(color=self.color['logembed_color'], description=f"{emotes.red_mark} Command **{command}** doesn't exist.")
            return await ctx.send(embed=embed)

        if cmd.parent:
            if await self.bot.db.fetchval("SELECT * FROM cmds WHERE command = $1", str(f"{cmd.parent} {cmd.name}")) is None:
                await self.bot.db.execute("INSERT INTO cmds(command) VALUES ($1)", str(f"{cmd.parent} {cmd.name}"))
                return await ctx.send(f"{emotes.white_mark} Okay. **{cmd.parent} {cmd.name}** was disabled.")
            elif await self.bot.db.fetchval("SELECT * FROM cmds WHERE command = $1", str(f"{cmd.parent} {cmd.name}")):
                return await ctx.send(f"{emotes.warning} | `{cmd.parent} {cmd.name}` is already disabled")
        elif not cmd.parent:
            if await self.bot.db.fetchval("SELECT * FROM cmds WHERE command = $1", str(cmd.name)) is None:
                await self.bot.db.execute("INSERT INTO cmds(command) VALUES ($1)", str(cmd.name))
                return await ctx.send(f"{emotes.white_mark} Okay. **{cmd.name}** was disabled.")
            elif await self.bot.db.fetchval("SELECT * FROM cmds WHERE command = $1", str(cmd.name)):
                return await ctx.send(f"{emotes.warning} | `{cmd.name}` is already disabled")


    @dev.command(brief="Enable disabled cmd")
    async def enablecmd(self, ctx, *, command):
        """Enables a disabled command"""
        cmd = self.bot.get_command(command)

        if cmd is None:
            embed = discord.Embed(color=self.color['logembed_color'], description=f"{emotes.red_mark} Command **{command}** doesn't exist.")
            return await ctx.send(embed=embed)

        if cmd.parent:
            if await self.bot.db.fetchval("SELECT * FROM cmds WHERE command = $1", str(f"{cmd.parent} {cmd.name}")) is None:
                return await ctx.send(f"{emotes.warning} | `{cmd.parent} {cmd.name}` is not disabled!")
            elif await self.bot.db.fetchval("SELECT * FROM cmds WHERE command = $1", str(f"{cmd.parent} {cmd.name}")):
                await self.bot.db.execute("DELETE FROM cmds WHERE command = $1", str(f"{cmd.parent} {cmd.name}"))
                return await ctx.send(f"{emotes.white_mark} | `{cmd.parent} {cmd.name}` is now enabled!")
        elif not cmd.parent:
            if await self.bot.db.fetchval("SELECT * FROM cmds WHERE command = $1", str(cmd.name)) is None:
                return await ctx.send(f"{emotes.warning} | `{cmd.name}` is not disabled!")
            elif await self.bot.db.fetchval("SELECT * FROM cmds WHERE command = $1", str(cmd.name)):
                await self.bot.db.execute("DELETE FROM cmds WHERE command = $1", str(cmd.name))
                return await ctx.send(f"{emotes.white_mark} | `{cmd.name}` is now enabled!")
    
    @dev.command(brief="Disabled commands list")
    async def disabledcmds(self, ctx):
        try:
            cmd = []
            for command, in await self.bot.db.fetch("SELECT command FROM cmds"):
                cmd.append(command) 

            if len(cmd) == 0:
                return await ctx.send("No disabled commands.") 
                
            cmds = []  # Let's list the guilds
            for command in cmd:
                cmds.append(f'{command}')
                
                
            e = discord.Embed(color=self.color['embed_color'], title="Disabled commands", description="`" + '`, `'.join(cmds) + '`')
            await ctx.send(embed=e)
        
        except Exception as e:
            await ctx.send(e)
    
    @dev.command(brief='Put bot into maintenance mode')
    async def maintenance(self, ctx):
        
        if self.bot.lockdown == 'True':
            self.bot.lockdown = 'False'
            await ctx.send(f"{emotes.white_mark} Bot is out of maintenance mode now.")
        elif self.bot.lockdown == 'False':
            self.bot.lockdown = 'True'
            await ctx.send(f"{emotes.white_mark} Bot is in maintenance mode now.")


# ! Cog managment
    @dev.group(brief="Cog managment", description="Manage cogs.")
    async def cog(self, ctx):
        """ Cog managment commands.
        cog r <cog> to reload already loaded cog.
        cog l <cog> to load unloaded cog.
        cog u <cog> to unload loaded cog."""
        if ctx.invoked_subcommand is None:
            pass

    @cog.command(aliases=["l"], brief="Load cog", description="Load any cog")
    async def load(self, ctx, name: str):
        """ Reloads an extension. """
        try:
            self.bot.load_extension(f"cogs.{name}")
        except Exception as e:
            return await ctx.send(f"```py\n{e}```")
        await ctx.send(f"📥 Loaded extension **cogs/{name}.py**")


    @cog.command(aliases=["r"], brief="Reload cog", description="Reload any cog")
    async def reload(self, ctx, name: str):
        """ Reloads an extension. """

        try:
            self.bot.reload_extension(f"cogs.{name}")
            await ctx.send(f"🔁 Reloaded extension **cogs/{name}.py**")

        except Exception as e:
            return await ctx.send(f"```py\n{e}```")

    @cog.command(aliases=['u'], brief="Unload cog", description="Unload any cog")
    async def unload(self, ctx, name: str):
        """ Reloads an extension. """
        try:
            self.bot.unload_extension(f"cogs.{name}")
        except Exception as e:
            return await ctx.send(f"```py\n{e}```")
        await ctx.send(f"📤 Unloaded extension **cogs/{name}.py**")
    
    @cog.command(aliases=['ra'], brief="Reload all cogs")
    async def reloadall(self, ctx):
        """ Reloads all extensions. """
        error_collection = []
        for file in os.listdir("cogs"):
            if file.endswith(".py"):
                name = file[:-3]
                try:
                    self.bot.reload_extension(f"cogs.{name}")
                except Exception as e:
                    error_collection.append(
                        [file, default.traceback_maker(e, advance=False)]
                    )

        if error_collection:
            output = "\n".join([f"**{g[0]}** ```diff\n- {g[1]}```" for g in error_collection])
            return await ctx.send(
                f"Attempted to reload all extensions, was able to reload, "
                f"however the following failed...\n\n{output}"
            )

        await ctx.send("Successfully reloaded all extensions")
    
# ! Utils
     
    @dev.command(aliases=['ru'])
    async def reloadutils(self, ctx, name: str):
        """ Reloads a utils module. """
        name_maker = f"utils/{name}.py"
        try:
            module_name = importlib.import_module(f"utils.{name}")
            importlib.reload(module_name)
        except ModuleNotFoundError:
            return await ctx.send(f"Couldn't find module named **{name_maker}**")
        except Exception as e:
            error = default.traceback_maker(e)
            return await ctx.send(f"Module **{name_maker}** returned error and was not reloaded...\n{error}")
        await ctx.send(f"🔁 Reloaded module **{name_maker}**")

# ! Admins
    
    @dev.command(hidden=True)
    async def adminadd(self, ctx, user: discord.User):
        owner=await self.bot.db.fetchval("SELECT user_id FROM admins WHERE user_id = $1", user.id)

        if owner is None:
            await self.bot.db.execute("INSERT INTO admins(user_id) VALUES ($1)", user.id)
            self.bot.admins.append(user.id)
            await ctx.send(f"Done! Added **{user}** to my admins list")

        if owner is not None:
            await ctx.send(f"**{user}** is already in my admins list")

    @dev.command(hidden=True)
    async def adminremove(self, ctx, user: discord.User):

        owner=await self.bot.db.fetchval("SELECT user_id FROM admins WHERE user_id = $1", user.id)

        if owner is not None:
            await self.bot.db.execute("DELETE FROM admins WHERE user_id = $1", user.id)
            self.bot.admins.remove(user.id)
            await ctx.send(f"Done! Removed **{user}** from my admins list")

        if owner is None:
            await ctx.send(f"**{user}** is not in my admins list")

    @dev.command()
    async def adminlist(self, ctx):
        users = [] 
        for num, data in enumerate(await self.bot.db.fetch("SELECT user_id FROM admins"), start=1):
            users.append(f"`[{num}]` | **{await self.bot.fetch_user(data['user_id'])}** ({data['user_id']})\n")
        
    

        e = discord.Embed(color=self.color['embed_color'], title="Bot admins", description="".join(users))
        await ctx.send(embed=e)

    @dev.command()
    async def logout(self, ctx):

        await ctx.send("Logging out now..")
        await self.bot.session.close()
        await self.bot.logout()

    @commands.command(hidden=True)
    async def post(self, ctx: commands.Context):
        """
        Manually posts guild count using discordlists.py (BotBlock)
        """
        try:
            result = await self.api.post_count()
        except Exception as e:
            try:
                await ctx.send("Request failed: `{}`".format(e))
                return
            except:
                channel = self.bot.get_channel(703627099180630068)
                s = default.traceback_maker(e, advance=False)
                print(s)
                await channel.send(default.error_send('Posting everything failed!', s))
                return

        print(result['failure'])
        await ctx.send("Successfully manually posted server count ({:,}) to {:,} lists."
                       "\nFailed to post server count to {} lists.".format(self.api.server_count,
                                                                             len(result["success"].keys()),
                                                                             len(result["failure"].keys())))

# Badges

    @commands.group(name="add-badge", aliases=['addbadge', 'abadge'], invoke_without_command=True)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def add_badge(self, ctx):
        await ctx.send_help(ctx.command)

    @add_badge.command(name="user", aliases=['u'])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def add_badge_user(self, ctx, user: discord.User, badge):
        with open('db/badges.json', 'r') as f:
            data = json.load(f)

        avail_badges = ['bot_early_supporter', 'bot_admin', 'bot_owner','bot_partner', 'bot_booster', 'bot_verified', 'discord_bug1', 'discord_bug2']
        if badge.lower() not in avail_badges:
            return await ctx.send(f"{emotes.warning} **Invalid badge! Here are the valid ones:** {', '.join(avail_badges)}", delete_after=20)

        if badge.lower() == "bot_early_supporter":
            badge = emotes.bot_early_supporter
        elif badge.lower() == "bot_partner":
            badge = emotes.bot_partner
        elif badge.lower() == "bot_booster":
            badge = emotes.bot_booster
        elif badge.lower() == "bot_verified":
            badge = emotes.bot_verified
        elif badge.lower() == "bot_admin":
            badge = emotes.bot_admin
        elif badge.lower() == "bot_owner":
            badge = emotes.bot_owner
        elif badge.lower() == "discord_bug1":
            badge = emotes.discord_bug1
        elif badge.lower() == "discord_bug2":
            badge = emotes.discord_bug2

        try:
            if badge in data['Users'][f'{user.id}']["Badges"]:
                return await ctx.send(f"{emotes.warning} {user} already has {badge} badge")
            elif badge not in data['Users'][f'{user.id}']["Badges"]:
                data['Users'][f'{user.id}']["Badges"] += [badge]
                self.bot.user_badges[f"{user.id}"]["Badges"] += [badge]
        except KeyError:
            data['Users'][f"{user.id}"] = {"Badges": [badge]}
            self.bot.user_badges[f"{user.id}"] = {"Badges": [badge]}

        with open('db/badges.json', 'w') as f:
            data = json.dump(data, f, indent=4)

        await ctx.send(f"{emotes.white_mark} Added {badge} to {user}.")
    
    @add_badge.command(name='server', aliases=['g'])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def add_badge_server(self, ctx, guild: str, badge):
        if not guild.isdigit():
            return await ctx.send(f"{emotes.warning} That's not an id")
        try:
            guild = self.bot.get_guild(int(guild))
            
            with open('db/badges.json', 'r') as f:
                data = json.load(f)

            avail_badges = ['server_partner', 'bot_verified']
            if badge.lower() not in avail_badges:
                return await ctx.send(f"{emotes.warning} **Invalid badge! Here are the valid ones:** {', '.join(avail_badges)}", delete_after=20)

            if badge.lower() == "server_partner":
                badge = emotes.server_partner
            elif badge.lower() == "bot_verified":
                badge = emotes.bot_verified

            try:
                if badge in data['Servers'][f'{guild.id}']["Badges"]:
                    return await ctx.send(f"{emotes.warning} {guild} already has {badge} badge")
                elif badge not in data['Servers'][f'{guild.id}']["Badges"]:
                    data['Servers'][f'{guild.id}']["Badges"] += [badge]
            except KeyError:
                data['Servers'][f"{guild.id}"] = {"Badges": [badge]}

            with open('db/badges.json', 'w') as f:
                data = json.dump(data, f, indent=4)
            await ctx.send(f"{emotes.white_mark} Added {badge} to {guild}.")
        except AttributeError:
            return await ctx.send(f"{emotes.warning} Can't seem to find that guild, are you sure the ID is correct?")
    
    @commands.group(name="remove-badge", aliases=['removebadge', 'rbadge'], invoke_without_command=True)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def remove_badge(self, ctx):
        await ctx.send_help(ctx.command)

    @remove_badge.command(name="user", aliases=['u'])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def remove_badge_user(self, ctx, user: discord.User, badge):
        with open('db/badges.json', 'r') as f:
            data = json.load(f)

        avail_badges = ['bot_early_supporter', 'bot_admin', 'bot_owner','bot_partner', 'bot_booster', 'bot_verified', 'discord_bug1', 'discord_bug2', 'blacklisted']
        if badge.lower() not in avail_badges:
            return await ctx.send(f"{emotes.warning} **Invalid badge! Here are the valid ones:** {', '.join(avail_badges)}", delete_after=20)

        if badge.lower() == "bot_early_supporter":
            badge = emotes.bot_early_supporter
        elif badge.lower() == "bot_partner":
            badge = emotes.bot_partner
        elif badge.lower() == "bot_booster":
            badge = emotes.bot_booster
        elif badge.lower() == "bot_verified":
            badge = emotes.bot_verified
        elif badge.lower() == "bot_admin":
            badge = emotes.bot_admin
        elif badge.lower() == "bot_owner":
            badge = emotes.bot_owner
        elif badge.lower() == "discord_bug1":
            badge = emotes.discord_bug1
        elif badge.lower() == "discord_bug2":
            badge = emotes.discord_bug2
        elif badge.lower() == "blacklisted":
            badge = emotes.blacklisted

        try:
            if len(data['Users'][f'{user.id}']["Badges"]) < 2:
                data['Users'].pop(f"{user.id}")
                self.bot.user_badges.pop(f"{user.id}")
            else:
                data['Users'][f'{user.id}']["Badges"].remove(badge)
                self.bot.user_badges[f"{user.id}"]["Badges"].remove(badge)
        except Exception as e:
            return await ctx.send(f"{emotes.warning} {user} has no badges! {e}")

        with open('db/badges.json', 'w') as f:
            data = json.dump(data, f, indent=4)

        await ctx.send(f"{emotes.white_mark} Removed {badge} from {user}.")
    
    @remove_badge.command(name='server', aliases=['g'])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def remove_badge_server(self, ctx, guild: str, badge):
        if not guild.isdigit():
            return await ctx.send(f"{emotes.warning} That's not an id")
        try:
            guild = self.bot.get_guild(int(guild))
            
            with open('db/badges.json', 'r') as f:
                data = json.load(f)

            avail_badges = ['server_partner', 'bot_verified']
            if badge.lower() not in avail_badges:
                return await ctx.send(f"{emotes.warning} **Invalid badge! Here are the valid ones:** {', '.join(avail_badges)}", delete_after=20)

            if badge.lower() == "server_partner":
                badge = emotes.server_partner
            elif badge.lower() == "bot_verified":
                badge = emotes.bot_verified

            try:
                if len(data['Servers'][f'{guild.id}']["Badges"]) < 2:
                    data['Servers'].pop(f"{guild.id}")
                else:
                    data['Server'][f'{guild.id}']["Badges"].remove(badge)
            except Exception as e:
                return await ctx.send(f"{emotes.warning} {guild} has no badges! `{e}`")

            with open('db/badges.json', 'w') as f:
                data = json.dump(data, f, indent=4)
            await ctx.send(f"{emotes.white_mark} Removed {badge} from {guild}.")
        except AttributeError:
            return await ctx.send(f"{emotes.warning} Can't seem to find that guild, are you sure the ID is correct?")

    @dev.command(brief='Add booster', name='add-booster', aliases=['addbooster', 'aboost'])
    async def add_booster(self, ctx, user: discord.User):
        check = await self.bot.db.fetchval("SELECT * FROM vip WHERE user_id = $1", user.id)

        if check:
            return await ctx.send(f"{emotes.warning} {user} is already a booster!")
        with open('db/badges.json', 'r') as f:
            data = json.load(f)
        badge = emotes.bot_booster
        try:
            if badge not in data['Users'][f'{user.id}']["Badges"]:
                data['Users'][f'{user.id}']["Badges"] += [badge]
        except KeyError:
            data['Users'][f"{user.id}"] = {"Badges": [badge]}

        with open('db/badges.json', 'w') as f:
            data = json.dump(data, f, indent=4)
        await self.bot.db.execute("INSERT INTO vip(user_id, prefix) VALUES($1, $2)", user.id, '-')
        self.bot.boosters[user.id] = {'custom_prefix': '-'}
        g = self.bot.get_guild(671078170874740756)
        role = g.get_role(686259869874913287)
        m = g.get_member(user.id)
        try:
            await m.add_roles(role)
        except:
            pass

        await ctx.send(f"{emotes.white_mark} Added {user.mention} ({user} ({user.id})) to boosters list!")
    
    @dev.command(brief='Remove booster', name='remove-booster', aliases=['removebooster', 'rboost'])
    async def remove_booster(self, ctx, user: discord.User):
        check = await self.bot.db.fetchval("SELECT * FROM vip WHERE user_id = $1", user.id)

        if not check:
            return await ctx.send(f"{emotes.warning} {user} is not a booster!")
        with open('db/badges.json', 'r') as f:
            data = json.load(f)
        badge = emotes.bot_booster
        try:
            if badge in data['Users'][f'{user.id}']["Badges"]:
                data['Users'][f'{user.id}']["Badges"].remove(badge)
        except KeyError:
            pass

        with open('db/badges.json', 'w') as f:
            data = json.dump(data, f, indent=4)
        await self.bot.db.execute("DELETE FROM vip WHERE user_id = $1", user.id)
        self.bot.boosters.pop(user.id)
        g = self.bot.get_guild(671078170874740756)
        role = g.get_role(686259869874913287)
        m = g.get_member(user.id)
        try:
            await m.remove_roles(role)
        except:
            pass

        await ctx.send(f"{emotes.white_mark} Removed {user.mention} ({user} ({user.id})) from boosters list!")
    
    @commands.group(brief='Manage partners', invoke_without_command=True)
    async def partner(self, ctx):
        """ Manage partners """
        await ctx.send_help(ctx.command)
    
    @partner.command(brief='Add a partner', name='add')
    async def partner_add(self, ctx, partner: discord.User, ptype: str):

        if partner.bot:
            return await ctx.send(f"{emotes.red_mark} Can't let you do that! It's a bot!")
        
        with open('db/badges.json', 'r') as f:
            data = json.load(f)
        badge = emotes.bot_partner
        # try:
        #     if badge in data['Users'][f'{partner.id}']["Badges"]:
        #         return await ctx.send(f"{emotes.warning} User is already our partner!")
        # except KeyError:
        #     pass
        try:
            def check(m):
                return m.author == ctx.author and m.channel.id == ctx.channel.id
            
            def check2(r, u):
                return u.id == ctx.author.id and r.message.id == msg.id
            
            support_server = self.bot.get_guild(671078170874740756)
            partner_channel = support_server.get_channel(698903601933975625)
            partner_remind_role = support_server.get_role(741749103280783380)
            partner_role = support_server.get_role(683288670467653739)
            partner_member = support_server.get_member(partner.id)

            msg = await ctx.channel.send(f"{emotes.loading2} Waiting for partner message...")
            message = await self.bot.wait_for('message', check=check)

            e = discord.Embed(color=self.color['embed_color'], title='Are you sure?')
            if message.content.lower() == "cancel":
                await message.delete()
                return await msg.edit(content=f"{emotes.white_mark} Cancelled..", delete_after=15)
            else:
                e.description = f"{message.content}"
            
            await msg.edit(content='', embed=e)
            await msg.add_reaction(f"{emotes.white_mark}")
            await msg.add_reaction(f"{emotes.red_mark}")
            react, user = await self.bot.wait_for('reaction_add', check=check2)

            if str(react) == f"{emotes.white_mark}":
                with open('db/badges.json', 'r') as f:
                    data = json.load(f)
                badge = emotes.bot_partner
                try:
                    if badge not in data['Users'][f'{partner.id}']["Badges"]:
                        data['Users'][f'{partner.id}']["Badges"] += [badge]
                        self.bot.user_badges[f"{partner.id}"]["Badges"] += [badge]
                except KeyError:
                    data['Users'][f"{partner.id}"] = {"Badges": [badge]}
                    self.bot.user_badges[f"{partner.id}"] = {"Badges": [badge]}

                with open('db/badges.json', 'w') as f:
                    data = json.dump(data, f, indent=4)
                
                msgs = f"{partner_remind_role.mention}\n\n{message.content}"
                try:
                    await partner_member.add_roles(partner_role, reason='user is now a our partner!')
                except Exception as e:
                    print(default.traceback_maker(e, advance=True))
                    pass
                try:
                    await partner.send(f"{emotes.bot_partner} Congratulations! You're now partnered with me!")
                except:
                    pass

                await partner_channel.send(content=msgs, allowed_mentions=discord.AllowedMentions(roles=True))

                try:
                    await msg.clear_reactions()
                except:
                    pass
                await self.bot.db.execute("INSERT INTO partners(user_id, partner_type, partner_message, partnered_since) VALUES($1, $2, $3, $4)", partner.id, ptype, message.content, datetime.now())
                return await msg.edit(content="OK!", embed=None)
                
            elif str(react) == f"{emotes.red_mark}":
                try:
                    await msg.clear_reactions()
                except:
                    pass
                return await msg.edit(content='Sure, reinvoke this command then.', embed=None)
        except Exception as e:
            return await ctx.send(default.traceback_maker(e, advance=True))
    
    @partner.command(brief='Remove a partner', name='remove')
    async def partner_remove(self, ctx, partner: discord.User):
        with open('db/badges.json', 'r') as f:
            data = json.load(f)
        badge = emotes.bot_partner
        try:
            if badge not in data['Users'][f'{partner.id}']["Badges"]:
                return await ctx.send(f"{emotes.warning} User is not our partner!")
        except KeyError:
            pass

        support_server = self.bot.get_guild(671078170874740756)
        partner_channel = support_server.get_channel(698903601933975625)
        partner_role = support_server.get_role(683288670467653739)
        partner_member = support_server.get_member(partner.id)

        try:
            data['Users'][f'{partner.id}']['Badges'].remove(badge)
            self.bot.user_badges[f'{partner.id}']['Badges'].remove(badge)
        except KeyError:
            pass
        with open('db/badges.json', 'w') as f:
           data = json.dump(data, f, indent=4)
        if partner_member:
            await partner_member.remove_roles(partner_role, reason='user is not our partner no more')

        await ctx.send(f"{emotes.white_mark} Removed {partner} from our partner list. Now go ahead and delete their partner message in {partner_channel.mention} if you haven't yet.")
        await self.bot.db.execute("DELETE FROM partners WHERE user_id = $1", partner.id)

def setup(bot):
    bot.add_cog(owner(bot))
