import DBA
import secretly
import discord
import csv
import datetime
import time
import asyncio
from bing_image_urls import bing_image_urls
from discord.ui import Button, View
from discord.ext import commands, tasks

GUILDS=[242403504839327744, 1052203385790677053]

intents = discord.Intents(message_content=True, messages=True, guilds=True, reactions=True, members=True)
client = discord.Bot(intents=intents, activity=discord.Game(str('/roll a waifu or /confess your sins >:3')))

@client.event
async def on_raw_reaction_add(payload):
    channel = client.get_channel(payload.channel_id)
    try:
        message = await channel.fetch_message(payload.message_id)
        embed = message.embeds[0]
        dic = embed.to_dict()
        # print(dic)
        waifu = dic['footer']['text']
        name = dic['title']
        # Get current time
        unix_time_now = await get_unix_time_now()
        # compare against claim time limit
        with DBA.DBAccess() as db:
            temp = db.query('SELECT claim_time_limit, user_id FROM waifu WHERE id = %s;', (waifu,))
            limit = temp[0][0]
            belongs_to = temp[0][1]
        if unix_time_now > limit:
            return
        if belongs_to:
            return
        # insert new user into db if they dont exist yet
        x = await check_if_uid_exists(payload.user_id)
        if x:
            pass
        else:
            with DBA.DBAccess() as db:
                db.execute('INSERT INTO user (id) VALUES (%s);', (payload.user_id,))
        with DBA.DBAccess() as db:
            db.execute('UPDATE waifu SET user_id = %s WHERE id = %s;', (payload.user_id, waifu))
        await channel.send(f'💖<@{payload.user_id}> and **{name}** are now married!💖')
        return
    except Exception as e:
        # await channel.send(e)
        return
    # print(dic['footer']['text'])
    # print(embed.to_dict())

@client.slash_command(
    name='roll',
    description='roll',
    guild_ids=GUILDS
)
async def roll(ctx):
    await ctx.defer()
    with DBA.DBAccess() as db:
        # Roll for a waifu that isn't taken
        temp = db.query('SELECT id, name, series FROM waifu WHERE user_id IS NULL ORDER BY RAND() LIMIT 1;', ())
        # print(temp)
        # print('aaaaaaaaaaaaaaaaaaaaaaa')
        waifu = temp[0][0]
        name = temp[0][1]
        series = temp[0][2]
        unix_time_now = await get_unix_time_now()
        unix_time_now+=60
        db.execute('UPDATE waifu SET claim_time_limit = %s WHERE id = %s;', (unix_time_now, waifu))
    url = bing_image_urls(f'{name} {series}', limit=1)[0]
    embed = discord.Embed(title=name, description=f'{series}\n\nReact with any emoji to claim!', color=discord.Colour.random())
    embed.set_image(url=url)
    embed.set_footer(text=waifu)
    await ctx.respond(embed=embed)

@client.slash_command(
    name='collection',
    description='view your collection',
    guild_ids=GUILDS
)
async def collection(ctx):
    await ctx.defer(ephemeral=True)
    data = []
    with DBA.DBAccess() as db:
        temp = db.query('SELECT name FROM waifu WHERE user_id = %s;', (ctx.author.id,))
    for i in temp:
        data.append(i[0])
    # print(data)
    data = [data[i:i+10] for i in range(0, len(data), 10)]
    page = 0
    max_pages = len(data) - 1
    embed = discord.Embed(title="Collection:", description="Showing page {}/{}".format(page+1, max_pages+1))
    embed.add_field(name="💞", value="\n".join(data[page]))
    search_string = data[page][0]
    # print(search_string)
    url = bing_image_urls(search_string, limit=1)[0]
    embed.set_thumbnail(url=url)
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("⏮️")
    await msg.add_reaction("⬅️")
    await msg.add_reaction("➡️")
    await msg.add_reaction("⏭️")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["⏮️", "⬅️", "➡️", "⏭️"]
    await ctx.respond('collection requested...')
    while True:
        try:
            reaction, user = await client.wait_for("reaction_add", check=check, timeout=60.0)
        except asyncio.TimeoutError:
            await msg.clear_reactions()
            return
        else:
            if str(reaction.emoji) == "⏮️":
                page = 0
            elif str(reaction.emoji) == "⬅️":
                if page == 0:
                    page = max_pages
                else:
                    page -= 1
            elif str(reaction.emoji) == "➡️":
                if page == max_pages:
                    page = 0
                else:
                    page += 1
            elif str(reaction.emoji) == "⏭️":
                page = max_pages
            if user != client.user:
                await reaction.remove(user)
            embed = discord.Embed(title="Collection", description="Showing page {}/{}".format(page+1, max_pages+1))
            embed.add_field(name="💞", value="\n".join(data[page]))
            search_string = data[page][0]
            # print(search_string)
            url = bing_image_urls(search_string, limit=1)[0]
            embed.set_thumbnail(url=url)
            await msg.edit(embed=embed)

@client.slash_command(
    name='divorce',
    description='divorce someone',
    guild_ids=GUILDS
)
async def divorce(
    ctx,
    name: discord.Option(str, 'name of character to divorce', required=True)):
    await ctx.defer()
    with DBA.DBAccess() as db:
        temp = db.query('SELECT id, name FROM waifu WHERE user_id = %s AND name LIKE %s;', (ctx.author.id, f'%{name}%'))
        waifu = temp[0][0]
        waifu_name = temp[0][1]
        db.execute('UPDATE waifu SET user_id = NULL WHERE id = %s;', (waifu,))
    await ctx.respond(f'<@{ctx.author.id}> has divorced {waifu_name}')

@client.slash_command(
    name='confess',
    description=':x',
    guild_ids=GUILDS
)
async def confess(
    ctx,
    message: discord.Option(str, 'say it', required=True)):
    await ctx.defer(ephemeral=True)
    try:
        channel = client.get_channel(secretly.confession_channel)
        await channel.send(message)
        await ctx.respond('Your confession was submitted! :x')
    except Exception as e:
        await ctx.respond(f'Oops! Error... Sorry: `{e}`')
    return



#  helpers
async def get_unix_time_now():
    return time.mktime(datetime.datetime.now().timetuple())

async def check_if_uid_exists(uid):
    try:
        with DBA.DBAccess() as db:
            temp = db.query('SELECT id FROM user WHERE id = %s;', (uid, ))
            if temp[0][0] == uid:
                return True
            else:
                return False
    except Exception:
        return False

client.run(secretly.token)