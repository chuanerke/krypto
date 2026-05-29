import discord
from discord.ext import commands
import db
import sqlite3


class Alerts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="alert")
    async def alert(self, ctx, action, *args):
        action = action.lower()

        if action == "set":
            symbol = args[0].upper()
            direction = args[1].lower()

            target_price = float(args[2])

            if direction not in ("above", "below"):
                await ctx.send("Direction must be `above` or `below`.")
                return

            if symbol not in db.get_crypto_sym():
                await ctx.send(f"`{symbol}` is not a tracked crypto.")
                return

            user_id = db.get_or_create_user(ctx.author.id)
            crypto_id = db.get_id_from_sym(symbol)
            db.add_alert(user_id, crypto_id, direction, target_price, 1)

            await ctx.send(f"Alert set: {symbol} goes {direction} {target_price}")

        elif action == "list":
            user_id = db.get_or_create_user(ctx.author.id)
            alerts = db.get_alerts(user_id)

            if not alerts:
                await ctx.send("You have no active alerts.")
                return

            lines = []
            # create table if not exists alerts (
            #     id integer primary key autoincrement,
            #     user_id integer,
            #     crypto_id integer,
            #     direction text not null check(direction in ('above', 'below')),
            #     target_price real not null,
            #     active boolean default 1,
            #     foreign key(user_id) references users(id) on delete cascade,
            #     foreign key(crypto_id) references crypto(id) on delete cascade
            # );
            for a in alerts:
                sym = db.get_sym_from_id(a[2])
                status = "active" if a[5] else "triggered"
                lines.append(f"{a[0]} — {sym} {a[3]} {a[4]} [{status}]")
            embed = discord.Embed(title="Your Alerts", description="\n".join(lines))
            await ctx.send(embed=embed)

        elif action == "remove":
            alert_id = int(args[0])

            user_id = db.get_or_create_user(ctx.author.id)
            db.remove_alert(alert_id, user_id)
            await ctx.send(f"Alert #{alert_id} removed.")


async def setup(bot):
    await bot.add_cog(Alerts(bot))