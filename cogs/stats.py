import discord
from discord.ext import commands

import db
import aiosqlite

from datetime import datetime
from datetime import timedelta

class Stats(commands.Cog):
    """Stats of the database itself."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="stats", help="Gives the stats of the database so far.")
    async def stats(self, ctx):
        async with db.get_connection() as conn:
            # because coroutines so need await to finish first (hate)
            total_records = (await(await conn.execute("select count(*) from price_history")).fetchone())[0]
            total_cryptos = (await(await conn.execute("select count(*) from crypto")).fetchone())[0]
            latest_update = (await(await conn.execute("select max(history_date) from price_history")).fetchone())[0]

            await ctx.send(f"Cryptos tracked: {total_cryptos}\nPrice records: {total_records}\nLast update: {latest_update}")


    @commands.command(name="avg", help="Gives the average of a given crypto over a period of days.")
    async def avg(self, ctx, symbol, a_days: int):
        avg_id = await db.get_id_from_sym(symbol)
        current_date = datetime.now()

        start_date = current_date - timedelta(days=a_days)
        start_date = start_date.isoformat()

        current_date = current_date.isoformat()
        async with db.get_connection() as conn:
            average = (await(await conn.execute(f"select avg(open_price) from price_history where crypto_id = {avg_id} and history_date between '{start_date}' and '{current_date}'")).fetchone())[0]
            # conn.close()
            await ctx.send(f"**Average price of crypto {symbol + '-USD'}**: {average}")    

    @commands.command(name="users", help="Gives the information on the users added.")
    async def users(self, ctx):
        async with db.get_connection() as conn:
            total_users = (await conn.execute("select * from users")).fetchall()
            user_amt = (await(await conn.execute("select count(*) from users")).fetchone())[0]
            to_send = ""
            for i in range(user_amt):
                user = await self.bot.fetch_user(total_users[i][1])
                to_send += f"{total_users[i][0]}. {user}\n"
             
            return await ctx.send(to_send)
            

async def setup(bot):
    await bot.add_cog(Stats(bot))