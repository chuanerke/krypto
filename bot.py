import discord
from discord.ext import commands, tasks
from os import listdir
from itertools import cycle
import random
import db
import asyncio
from pretty_help import PrettyHelp


description = """
Krypto: A Cryptocurrency investment info bot
"""

def get_prefix(bot, message):
    if not isinstance(message.guild, discord.Guild):
        return '!'
    
    return ['!', '?', '>']

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=get_prefix, description=description, intents=intents, help_command=PrettyHelp())

async def load_extensions():
    for cog in listdir('./cogs'):
        if cog.endswith('.py') == True:
            await bot.load_extension(f'cogs.{cog[:-3]}')

@bot.event
async def on_ready():
    assert bot.user is not None

    print(f'Logged in as {bot.user} (ID = {bot.user.id})')
    print("-------")

    change_status.start()

status_list = cycle([
            'Working!',
            '(Maybe) Working!'
        ])

@tasks.loop(seconds=2)
async def change_status():
    await bot.change_presence(activity=discord.Game(next(status_list)))

@bot.command(description="Adds two numbers together")
async def add(ctx, left: int, right: int):
    await ctx.send(left + right)

@bot.command(description="Rolls NdN")
async def roll(ctx, dice: str):
    try:
        rolls, limits = map(int, dice.split('d'))
    except Exception:
        await ctx.send("Format has to be in NdN")
        return
    
    result = ', '.join(str(random.randint(1, limits)) for r in range(rolls))
    await ctx.send(result)

@bot.event
async def on_command_error(ctx, error):
    print(f"Error: {error}")
    await ctx.send(f"Error: {error}")

async def main():
    db.main()

    await load_extensions()
    token = str(input("Enter value of token: "))
    await bot.start(token)

asyncio.run(main())