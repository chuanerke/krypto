import discord
from discord.ext import commands

import db
import sqlite3

from datetime import datetime
from datetime import timedelta

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="stats", description="Gives the stats of the database so far")
    async def stats(self, ctx):
        with db.get_connection() as conn:
            total_records = conn.execute("select count(*) from price_history").fetchone()[0]
            total_cryptos = conn.execute("select count(*) from crypto").fetchone()[0]
            latest_update = conn.execute("select max(history_date) from price_history").fetchone()[0]

            await ctx.send(f"Cryptos tracked: {total_cryptos}\nPrice records: {total_records}\nLast update: {latest_update}")

    @commands.command(name="avg", description="Gives the average of a given crypto over a period of days")
    async def avg(self, ctx, symbol, a_days: int):
        avg_id = db.get_id_from_sym(symbol)
        current_date = datetime.now()

        start_date = current_date - timedelta(days=a_days)
        start_date = start_date.isoformat()

        current_date = current_date.isoformat()
        with db.get_connection() as conn:
            average = conn.execute(f"select avg(open_price) from price_history where crypto_id = {avg_id} and history_date between '{start_date}' and '{current_date}'").fetchone()[0]
            await ctx.send(f"**Average price of crypto {symbol + '-USD'}**: {average}`")    

    @commands.command(name="users")
    async def users(self, ctx):
        with db.get_connection() as conn:
            total_users = conn.execute("select * from users").fetchall()
            user_amt = conn.execute("select count(*) from users").fetchone()[0]
            to_send = ""
            for i in range(user_amt):
                user = await self.bot.fetch_user(total_users[i][1])
                to_send += f"{total_users[i][0]}. {user}\n"
             
            await ctx.send(to_send)

async def setup(bot):
    await bot.add_cog(Stats(bot))