from discord.ext import commands, tasks
import discord
import db
import yfinance as yf
import asyncio
import matplotlib.pyplot as plt
from matplotlib.dates import ConciseDateFormatter
import numpy as np
    

# import Paginator


# async def get_symbol_list():
#     # can't use async func globally (i think)
#     symbol_list = [sym + "-USB" async for sym in await db.get_crypto_sym()]
#     return symbol_list


# # Yahoo finance requirement (does not show up for WebSocket otherwise)
# symbol_list = None

# >>> dat.live()
# Connected to WebSocket.
# Subscribed to symbols: ['BTC-USD']
# Listening for messages...
# {'id': 'BTC-USD', 'price': 80950.95, 'time': '1778419338000', 'currency': 'USD', 'exchange': 'CCC', 'quote_type': 41, 
#'market_hours': 1, 'change_percent': 0.6958814, 'day_volume': '16655864832', 'day_high': 80922.92, 'day_low': 80558.07, 
#'change': 559.4297, 'open_price': 80655.64, 'last_size': '16655864832', 'price_hint': '2', 'vol_24hr': '16655864832', 
#'vol_all_currencies': '16655864832', 'from_currency': 'BTC', 'circulating_supply': 20027400.0, 'market_cap': 1620675790000.0}

class Price(commands.Cog):
    """Commands based on getting price information of different cryptocurrencies"""
    def __init__(self, bot):
        self.bot = bot
        self.stream_prices.start()

    @tasks.loop(count=1)
    async def stream_prices(self):
        # removed "async with await", might lead to error
        print("started")
        async with yf.AsyncWebSocket() as ws:
            try:
                await ws.subscribe(db.symbol_list)
                await ws.listen(self.on_price_update)
            except Exception as error:
                print(error)

    async def on_price_update(self, message):
        lp_id = await db.get_id_from_sym(message["id"][:-4])
        if await db.get_price_from_id(lp_id) != message["price"]:
            await db.update_live_price(lp_id, message["price"], message.get("change", 0), float(message.get("vol_24hr", 0)))

    @commands.command(name='price', help="Gives the current price of a cryptocurrency based on its symbol")
    async def price(self, ctx, symbol: str):
        info = (await asyncio.to_thread(lambda: yf.Ticker(symbol + "-USD"))).info
        print(info)
        #assert symbol + "-USD" not in symbol_list
        if (symbol + "-USD" not in db.symbol_list):
            if info:
                await db.update_crypto_list(symbol, info["name"])
                db.symbol_list.append(symbol + "-USD")
            else:
                await ctx.send("Symbol not found")
                return
        lp_id = await db.get_id_from_sym(symbol)
        # is insert or ignore, might take too much time, maybe change this part
        await db.update_live_price(lp_id, info["open"], 0.0, info["volume"])
        lp = (await db.get_table_data("live_prices", lp_id))
        to_send = f"SYMBOL: {symbol}, PRICE: {lp[1]}, CHANGE: {lp[2]}, VOLUME: {lp[3]}, LAST UPDATED: {lp[4]}"
        await ctx.send(to_send)        


    # {'Open': 
    #     {Timestamp('2026-05-07 00:00:00+0000', tz='UTC'): 81428.8515625, Timestamp('2026-05-08 00:00:00+0000', tz='UTC'): 80009.625, 
    #     Timestamp('2026-05-09 00:00:00+0000', tz='UTC'): 80187.7421875, Timestamp('2026-05-10 00:00:00+0000', tz='UTC'): 80655.640625}, 
    # 'High': 
    #     {Timestamp('2026-05-07 00:00:00+0000', tz='UTC'): 81684.953125, Timestamp('2026-05-08 00:00:00+0000', tz='UTC'): 80447.265625, 
    #     Timestamp('2026-05-09 00:00:00+0000', tz='UTC'): 81030.0625, Timestamp('2026-05-10 00:00:00+0000', tz='UTC'): 81482.5390625}, 
    # 'Low': 
    #     {Timestamp('2026-05-07 00:00:00+0000', tz='UTC'): 79522.65625, Timestamp('2026-05-08 00:00:00+0000', tz='UTC'): 79205.515625, 
    #     Timestamp('2026-05-09 00:00:00+0000', tz='UTC'): 80119.9296875, Timestamp('2026-05-10 00:00:00+0000', tz='UTC'): 80558.0703125}, 
    # 'Close': 
    #     {Timestamp('2026-05-07 00:00:00+0000', tz='UTC'): 80009.9921875, Timestamp('2026-05-08 00:00:00+0000', tz='UTC'): 80186.765625, 
    #     Timestamp('2026-05-09 00:00:00+0000', tz='UTC'): 80664.3671875, Timestamp('2026-05-10 00:00:00+0000', tz='UTC'): 81251.9921875}, 
    # 'Volume':
    #     {Timestamp('2026-05-07 00:00:00+0000', tz='UTC'): 36931193154, Timestamp('2026-05-08 00:00:00+0000', tz='UTC'): 33789351540, 
    #     Timestamp('2026-05-09 00:00:00+0000', tz='UTC'): 18102086996, Timestamp('2026-05-10 00:00:00+0000', tz='UTC'): 18724552704}, 
    # 'Dividends': 
    #     {Timestamp('2026-05-07 00:00:00+0000', tz='UTC'): 0.0, Timestamp('2026-05-08 00:00:00+0000', tz='UTC'): 0.0, 
    #     Timestamp('2026-05-09 00:00:00+0000', tz='UTC'): 0.0, Timestamp('2026-05-10 00:00:00+0000', tz='UTC'): 0.0}, 
    # 'Stock Splits':
    #     {Timestamp('2026-05-07 00:00:00+0000', tz='UTC'): 0.0, Timestamp('2026-05-08 00:00:00+0000', tz='UTC'): 0.0, 
    #     Timestamp('2026-05-09 00:00:00+0000', tz='UTC'): 0.0, Timestamp('2026-05-10 00:00:00+0000', tz='UTC'): 0.0}}
    async def add_to_history(self, symbol, days):
        ticker = yf.Ticker(symbol.upper() + "-USD")

        f_his = await asyncio.to_thread(lambda: ticker.history(period=str(days) + 'd'))
        # print(f_his)
        f_his_dict = f_his.to_dict()
        
        cry_id = await db.get_id_from_sym(symbol)
        # print(cry_id)


        prices = [[] for _ in range(5)]
        for key in f_his_dict["Open"].keys():
            prices[0].append(key.strftime('%Y-%m-%d'))
        
        for value in f_his_dict["Open"].values():
            prices[1].append(value)
        
        for value in f_his_dict["High"].values():
            prices[2].append(value)
        
        for value in f_his_dict["Low"].values():
            prices[3].append(value)
        
        for value in f_his_dict["Volume"].values():
            prices[4].append(value)

        
        for i in range(len(prices[0])):
            await db.update_price_history(cry_id, prices[0][i], prices[1][i], prices[2][i],
                                prices[3][i], prices[1][i], prices[4][i])
    

    async def add_to_embed(self, symbol, days: int):
        # his = db.get_table_data("price_history", db.get_id_from_sym(symbol))
        #await db.get_id_from_sym fixed Error: Command raised an exception: OperationalError: near "<": syntax error
        his = (await db.get_price_history(await db.get_id_from_sym(symbol), days))
        if his == [] or len(his) != days-1:
            await self.add_to_history(symbol, days)
            #same here
            his = await db.get_price_history(await db.get_id_from_sym(symbol), days)
        
        to_send = "```"

        embed = discord.Embed(
            title = f"{symbol}",
            description = f"Price history of {symbol} for the past {days} days"
        )

        his_val = [[], [], [], [], []]
        print(len(his))
        print(days)
        for i in range(len(his)):
            # to_send += f"Date: {his[i][2]} Open Price: {his[i][3]} High Price: {his[i][4]} Low Price: {his[i][5]} Volume: {his[i][7]}\n"
            his_val[0].append(str(his[i][2]))
            his_val[1].append(str(his[i][3]))
            his_val[2].append(str(his[i][4]))
            his_val[3].append(str(his[i][5]))
            his_val[4].append(str(his[i][7]))

        formatted_prod = [[], [], [], [], []]
        formatted_prod[0] = '\n'.join([f"{val}" for val in his_val[0]])
        formatted_prod[1] = '\n'.join([f"{round(float(val), 2)}" for val in his_val[1]])
        formatted_prod[2] = '\n'.join([f"{round(float(val), 2)}" for val in his_val[2]])
        formatted_prod[3] = '\n'.join([f"{round(float(val), 2)}" for val in his_val[3]])
        formatted_prod[4] = '\n'.join([f"{round(float(val), 2)}" for val in his_val[4]])



        embed.add_field(name="Date", value=f"**{formatted_prod[0]}**", inline="True")
        embed.add_field(name="Open Price", value=formatted_prod[1], inline="True")
        embed.add_field(name="Volume", value=formatted_prod[4], inline="True")
        embed.add_field(name="Date", value=f"**{formatted_prod[0]}**", inline="True")

        embed.add_field(name="High Price", value=formatted_prod[2], inline="True")
        embed.add_field(name="Low Price", value=formatted_prod[4], inline="True")

        return embed


    # @discord.ui.button(label="",style=discord.ButtonStyle.blurple,emoji="⬅️")
    # async def back_button(self, button:discord.ui.Button, interaction:discord.Interaction):
    #     button.disabled=True
    #     await interaction.response.edit_message(view=self)
    # @discord.ui.button(label="Gray Button",style=discord.ButtonStyle.gray,emoji="\U0001f974") # or .secondary/.grey
    # async def gray_button(self,button:discord.ui.Button,interaction:discord.Interaction):
    #     button.disabled=True
    #     await interaction.response.edit_message(view=self)


    # async def set_embed_buttons(self, embed):
    #     embed.set_footer()



    # @commands.command(name='history', help=
    #         """
    #             Gives the price history for a set amount of days for a cryptocurrency based on its symbol. 
    #             For e.g. ?history SHIB 42
    #         """
    #     )
    # async def history(self, ctx, symbol, days: int):
    #     # days += 1
        # if days < 10:
        #     await ctx.send(embed= await self.add_to_embed(symbol, days))
        #     return
        # embeds = []
        # embeds.append(await self.add_to_embed(symbol, days))
        # while True:
        #     days = days - 10
        #     if (days < 10):
        #         embeds.append(await self.add_to_embed(symbol, days))
        #         return
        #     else:
        #         embeds.append(await self.add_to_embed(symbol, 10))
        



        # DOES NOT FUCKING WORK
        # await Paginator.Simple().start(ctx, pages=embeds)
        
    
    @commands.command(name='compare', 
                help="Compares two cryptocurrencies together for a certain amount of days. For e.g. `?compare BTC ETH 5 ")
    async def compare(self, ctx, sym_1, sym_2, days: int):
        # days += 4 # idk why i'll see why later
        first_his = await db.get_price_history(await db.get_id_from_sym(sym_1), days)
        if first_his == [] or (len(first_his) != (days-1)):
            await self.add_to_history(sym_1, days)
            first_his = await db.get_price_history(await db.get_id_from_sym(sym_1), days)

        second_his = await db.get_price_history(await db.get_id_from_sym(sym_2), days)
        if second_his == [] or (len(second_his) != (days-1)):
            await self.add_to_history(sym_2, days)
            second_his = await db.get_price_history(await db.get_id_from_sym(sym_2), days)
        
        # print(first_his)
        # print("\n")
        # print(second_his)
        join_prod = (await db.join_compare(await db.get_id_from_sym(sym_1), await db.get_id_from_sym(sym_2), days))
        print(len(join_prod))
        # print(join_prod)
        prod_values = [[], [], []]
        for i in range(len(join_prod)):
            prod_values[0].append(join_prod[i][0])
            prod_values[1].append(join_prod[i][1])
            prod_values[2].append(join_prod[i][2])

        embed = discord.Embed(
            title = f"Comparison: {sym_1} vs {sym_2}"
        )
        formatted_prod = [[], [], []]
        formatted_prod[0] = '\n'.join([f"{val}" for val in prod_values[0]])
        formatted_prod[1] = '\n'.join([f"{val}" for val in prod_values[1]])
        formatted_prod[2] = '\n'.join([f"{val}" for val in prod_values[2]])
        # print(prod_values)

        embed.add_field(name="Date", value=formatted_prod[0], inline="True")
        embed.add_field(name=sym_1, value=formatted_prod[1], inline="True")
        embed.add_field(name=sym_2, value=formatted_prod[2], inline="True")

        print(prod_values)

        # np_date = np.asarray(prod_values[0])
        np_date = np.array(prod_values[0], dtype='datetime64')
        np_sym_1 = np.asarray(prod_values[1])
        np_sym_2 = np.asarray(prod_values[2])

        # fig, ax = plt.subplots(figsize=(5, 2.7))
        # x = np.arange(len(data1))
        # ax.plot(x, np.cumsum(data1), color='blue', linewidth=3, linestyle='--')
        # l, = ax.plot(x, np.cumsum(data2), color='orange', linewidth=2)
        # l.set_linestyle(':')
        fig, ax = plt.subplots(figsize=(40, 30))
        print(len(np_sym_1))
        x = np_date
        
        sym_max = max(max(np_sym_1), max(np_sym_2))
        sym_min = min(min(np_sym_1), min(np_sym_2))
        sym_sum = sum([(sum(np_sym_1) / len(np_sym_1)), (sum(np_sym_2) / len(np_sym_2))]) / 2
        print(sym_sum)

        # np_sym_1_range = np.arange(min(np_sym_1), max(np_sym_1), sum(np_sym_1) / len(np_sym_1))
        # np_sym_2_range = np.arange(min(np_sym_2), max(np_sym_2), sum(np_sym_2) / len(np_sym_2))

        ax.plot(x, np_sym_1, color='blue', linewidth=3, linestyle='--')
        l, = ax.plot(x, np_sym_2, color='orange', linewidth=2)
        l.set_linestyle(':')
        ax.xaxis.set_major_formatter(ConciseDateFormatter(ax.xaxis.get_major_locator()))
        # ax.set_yscale('log')
        ax.set_ylim(sym_min - sym_sum, sym_max + sym_sum) 



        plt.savefig(fname='/home/sgsk/Documents/file.png')


        await ctx.send(embed=embed)



async def setup(bot):
    # global symbol_list
    # symbol_list = await get_symbol_list()

    await bot.add_cog(Price(bot))