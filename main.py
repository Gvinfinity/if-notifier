import os
import discord
import asyncio
import datetime
import traceback
import json
import whatsapp
from discord.ext import commands, tasks
from get_news import get_news
from json import JSONEncoder
from news_class import dictToNews
from dotenv import load_dotenv

# Configura variaveis de ambiente
load_dotenv()

# Cria uma classe para permitir que as instâncias de News sejam serializadas
class NewsEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


bot = commands.Bot(command_prefix="&", intents=discord.Intents.all())
current_news = {}
db = []

def load_news():
    # Carrega da memória as notícias já enviadas
    global current_news
    db_file = open("db/current_news.json", "r")
    loaded_news = json.load(db_file)
    current_news = {}
    for k in loaded_news:
        l = []
        for e in loaded_news[k]:
            l.append(dictToNews(e))
        current_news[k] = l

def load_campi():
    #Carrega da memória o campus ligado à um ID
    global db
    db_file = open("db/db.json", "r")
    db = json.load(db_file)

def update_db():
    db_file = open("db/current_news.json", "w")
    json.dump(current_news, db_file, indent=6, cls=NewsEncoder)


async def send_news(nlist: list, guild):
    for n in nlist:
        embed = discord.Embed(
            colour=discord.Colour.dark_gold(),
            title=n.title,
            description=n.description,
            url=n.link
        )
        embed.set_image(url=n.thumbnail)
        channels = guild.text_channels
        for channel in channels:
            if channel.is_news():
                await channel.send(embed=embed)
                break


@tasks.loop(minutes=15.0)
async def update_news():
    load_news()
    global current_news
    for guild in bot.guilds:
        cnews_guild = current_news.get(str(guild.id), [])
        try:
            news = get_news(db[str(guild.id)])
        except Exception as e:
            print(type(e))
            traceback.print_exc()

        if not news:
            print(f"Not able to get news for: {guild.id}")
            
        # Create a list of news to send
        new_news = [n for n in news if n not in cnews_guild]

        if len(new_news) > 10:
            whatsapp.send_alert(guild.id)
            continue

        if new_news:
            updated = False
            try:
                await send_news(new_news, guild)
                if guild.id == 893328736051683329:
                    whatsapp.send_news(new_news)
            except Exception as e:
                print(e)
                print(type(e))
                traceback.print_exc()
        else:
            updated = True



        if not updated:
            current_news[str(guild.id)] = news
            update_db()
            log = open("debug.log", 'a')
            log.write(f"""
            LOG: Updated \"current_news\"\n
            NEWS_DB: {cnews_guild}\n\n""")
            log.close()

# Verifica quanto tempo até a próxima hora completa e dorme o loop até a mesma


@update_news.before_loop
async def looper():
    delta = datetime.timedelta(minutes=15)
    now = datetime.datetime.now()
    next_hour = (now + delta).replace(microsecond=0, second=0, minute=0)
    await asyncio.sleep((next_hour - now).seconds)


@bot.event
async def on_ready():
    print(f"Bot iniciado como: {bot.user}")
    load_news()


@bot.event
async def on_guild_join(guild):
    sys_channel = guild.system_channel
    db[guild.id] = "caruaru"
    
    with open("db/db.json", "w") as f:
        json.dump(db, f)

    if sys_channel:
        try:
            await sys_channel.send("Utilize o comando \"&alterarcampus (seucampus)\" para definir de qual campi as notificações serão enviadas!")
        except Exception as e:
            print(
                f"!!Não foi possível solicitar definição de campus no servidor: {guild.name}!!\nError:{e}\n\n")


@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def alterarcampus(ctx, campus):
    db[ctx.guild.id] = str(campus)
    
    with open("db/db.json", "w") as f:
        json.dump(db, f)

    await ctx.channel.send(f"Campus alterado com sucesso para {campus}")


@alterarcampus.error
async def alterarcampus_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        msg = "Você não tem permissão para executar essa ação, peça à um administrador!"
        await ctx.send(msg)


@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def atualizarmanual(ctx):
    global current_news
    guild_id = ctx.guild.id
    cnews_guild = current_news.get(str(guild_id))
    try:
        news = get_news(db[str(guild_id)])
    except Exception as e:
        print(type(e))
        traceback.print_exc()
    updated = True
    for n in news:
        if cnews_guild:
            verification = n not in cnews_guild
            if verification:
                updated = False
                await send_news(n, ctx.guild)
        else:
            try:
                updated = False
                await send_news(n, ctx.guild)
            except Exception as e:
                print(e)
                print(type(e))
                traceback.print_exc()

    if not updated:
        current_news[str(guild_id)] = news
        print(
            f"Manually updated by: {ctx.author}\n{datetime.datetime.now()}\n")
        try:
            update_db()
            await ctx.send("As notícias foram atualizadas com sucesso!")
        except Exception as e:
            print(e)
            print(type(e))
            traceback.print_exc()
    else:
        await ctx.send("Notícias já atualizadas!")


@atualizarmanual.error
async def atualizarmanual_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        msg = "Você não tem permissão para executar essa ação, peça à um administrador!"
        await ctx.send(msg)


@bot.command(pass_context=True)
async def massupdate(ctx):
    print(f"Mass update by: {ctx.author}")
    await update_news()

update_news.start()
bot.run(os.environ['DISCORD_BOT_TOKEN'])
