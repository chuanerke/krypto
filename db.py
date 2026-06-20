import aiosqlite
import asyncio
from pathlib import Path
from datetime import datetime
from datetime import timedelta

from contextlib import asynccontextmanager

DB_PATH = str(Path(__file__).parent / "krypto.db")
symbol_list = None

"""
https://docs.python.org/3/library/contextlib.html
other way get __aexit__ error
"""
@asynccontextmanager
async def get_connection():
    conn = await aiosqlite.connect(DB_PATH)
    await conn.execute("pragma foreign_keys = on")
    try:
        yield conn
    finally:
        await conn.commit()
        await conn.close()


async def init_db():
    async with get_connection() as conn:
        try:
            await conn.executescript("""
                create table if not exists crypto (
                    id integer primary key autoincrement,
                    symbol varchar(20) unique not null,
                    name varchar(100) not null,
                    added_at datetime default current_timestamp
                );

                create table if not exists users (
                    id integer primary key autoincrement,
                    discord_id varchar(100) unique not null,
                    created_at datetime default current_timestamp
                );

                create table if not exists price_history (
                    id integer primary key autoincrement,
                    crypto_id integer,
                    history_date date,
                    open_price real,
                    high_price real,
                    low_price real,
                    close_price real,
                    volume real,
                    unique(crypto_id, history_date),
                    foreign key(crypto_id) references crypto(id) on delete cascade
                );

                create table if not exists alerts (
                    id integer primary key autoincrement,
                    user_id integer,
                    crypto_id integer,
                    direction text not null check(direction in ('above', 'below')),
                    target_price real not null,
                    active boolean default 1,
                    foreign key(user_id) references users(id) on delete cascade,
                    foreign key(crypto_id) references crypto(id) on delete cascade
                );

                create table if not exists live_prices (
                    crypto_id integer primary key,
                    price real not null,
                    change_24h real,
                    volume_24h real,
                    last_updated datetime default current_timestamp,
                    foreign key(crypto_id) references crypto(id) on delete cascade
                );
            """)
        except aiosqlite.Error as err:
            print(err.sqlite_errorcode)
            print(err.sqlite_errorname)

        print("Database initialized")

async def insert_crypto_list():
    async with get_connection() as conn:
        alr_exists = (await(await conn.execute("select * from crypto")).fetchone())
        if alr_exists is None:
            await conn.executemany(
                "insert or ignore into crypto (symbol, name) values (?, ?)",
                [
                    ("BTC", "Bitcoin"),
                    ("ETH", "Ethereum"),
                    ("USDT", "Tether"),
                    ("XRP", "XRP"),
                    ("BNB", "BNB"),
                    ("USDC", "USD Coin"),
                    ("SOL", "Solana"),
                    ("TRX", "TRON"),
                    ("DOGE", "Dogecoin"),
                    ("HYPE", "Hyperliquid"),
                    ("ZEC", "Zcash"),
                    ("ADA", "Cardano"),
                    ("LEO", "UNUS SED LEO"),
                    ("BCH", "Bitcoin Cash"),
                    ("LINK", "Chainlink"),
                    ("XMR", "Monero"),
                    ("TON", "Toncoin"),
                    ("HBAR", "Hedera"),
                    ("XLM", "Stellar"),
                    ("DAI", "Dai"),
                ],
            )
        else:
            print("Initial crypto list already exists")

async def get_crypto_sym():
    async with get_connection() as conn:
        crypto_syms = (await(await conn.execute("select symbol from crypto")).fetchall())
        return [sym[0] for sym in crypto_syms]

async def get_price_from_id(lp_id):
    async with get_connection() as conn:
        ret_price = (await conn.execute("select price from live_prices where crypto_id = ?", (lp_id,))).fetchone()
        
        return ret_price[0] if ret_price else None

async def update_live_price(crypto_id, price, change_24h, volume_24h):
    async with get_connection() as conn:
        # changed current_timestamp to 'current_timestamp', might get error, remember (Changed, ProgrammingError)
        await conn.execute("""
            insert or replace into live_prices (crypto_id, price, change_24h, volume_24h, last_updated)
            values (?, ?, ?, ?, current_timestamp)""", 
            (crypto_id, price, change_24h, volume_24h))

async def get_table_data(table, lp_id):
    async with get_connection() as conn:
        if table == "live_prices":
            stm = (await(await conn.execute(f"select * from {table} where crypto_id = ?", (lp_id, ))).fetchone())
        else:
            stm = (await(await conn.execute(f"select * from {table} where crypto_id = ?", (lp_id, ))).fetchall())
        return stm

async def get_id_from_sym(sym: str):
    async with get_connection() as conn:
        val = (await conn.execute("select * from crypto where symbol = ?", (sym,)))
        val = (await val.fetchone())[0]
        
        return val


# create table if not exists price_history (
#                     id integer primary key autoincrement,
#                     crypto_id integer,
#                     history_date date,
#                     open_price real,
#                     high_price real,
#                     low_price real,
#                     close_price real,
#                     volume real,
#                     unique(crypto_id, history_date),
#                     foreign key(crypto_id) references crypto(id) on delete cascade
#                 );

async def update_price_history(crypto_id, history_date, open_price, high_price, low_price, close_price, volume):
    async with get_connection() as conn:
        await conn.execute("""
        insert or replace into price_history (crypto_id, history_date, open_price, high_price, low_price, close_price, volume)
        values(?, ?, ?, ?, ?, ?, ?)""",
        (crypto_id, history_date, open_price, high_price, low_price, close_price, volume))

async def get_price_history(crypto_id, p_dates: int):
    current_date = datetime.now()

    start_date = current_date - timedelta(days=p_dates)
    start_date = start_date.isoformat()

    current_date = current_date.isoformat()

    async with get_connection() as conn:
        stm = (await (await conn.execute(f"select * from price_history where crypto_id = {crypto_id} and history_date between '{start_date}' and '{current_date}' ")).fetchall())
        return stm

async def join_compare(id_1, id_2, p_dates: int):
    current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # it could be an issue of it being 12 AM right now. 
    start_date = current_date - timedelta(days=(p_dates + 1))
    start_date = start_date.isoformat()
    print(start_date)

    current_date = current_date.isoformat()
    print(current_date)

    # https://sqlblog.org/2009/10/16/bad-habits-to-kick-mis-handling-date-range-queries
    async with get_connection() as conn:
        return (await(await conn.execute(f"""
            select i1.history_date, i1.open_price, i2.open_price 
            from price_history i1 inner join price_history i2 on i1.history_date = i2.history_date where i1.crypto_id = {id_1} and i2.crypto_id = {id_2}
            and i1.history_date >= '{start_date}' and i1.history_date <= '{current_date}'""")).fetchall())


async def update_crypto_list(crypto_symbol, crypto_name):
    async with get_connection() as conn:
        await conn.execute("insert or ignore into crypto(symbol, name) values (?, ?)", (crypto_symbol, crypto_name, ))

async def get_sym_from_id(crypto_id):
    async with get_connection() as conn:
        return (await(await conn.execute("select symbol from crypto where id = ?", (crypto_id,))).fetchone())[0]


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
async def add_alert(user_id, crypto_id, direction, target_price, active):
    async with get_connection() as conn:
        await conn.execute("insert into alerts (user_id, crypto_id, direction, target_price, active) values (?,?,?,?,?)", 
                        (user_id, crypto_id, direction, target_price, active))

async def get_alerts(user_id):
    async with get_connection() as conn:
        return (await(await conn.execute(f"select * from alerts where user_id = {user_id}")).fetchall())

async def remove_alert(alert_id, user_id):
    async with get_connection() as conn:
        return await conn.execute(f"delete from alerts where id = {alert_id} and user_id = {user_id}")

async def check_alerts(crypto_id, current_price):
    async with get_connection() as conn:
        return (await(await conn.execute(f"""
            select * from alerts where crypto_id = {crypto_id} and active = 1
            and ((direction = 'above' and {current_price} >= target_price)
            or (direction = 'below' and {current_price} <= target_price))
        """)).fetchall())

async def deactivate_alert(alert_id):
    async with get_connection() as conn:
        await conn.execute("update alerts set active = 0 where id = ?", (alert_id,))

async def get_or_create_user(discord_id):
    async with get_connection() as conn:
        row = (await(await conn.execute(f"select id from users where discord_id = {str(discord_id)}")).fetchone())
        if row:
            return row[0]
        await conn.execute(f"insert into users (discord_id) values {str(discord_id)}")
        return (await(await conn.execute(f"select id from users where discord_id = {str(discord_id)}")).fetchone())[0]


async def main():
    db_path = Path(DB_PATH)
    global symbol_list
    #async with asyncio.connect(db_path)
    await init_db()
    await insert_crypto_list()
    symbol_list = [sym + "-USB"  for sym in (await get_crypto_sym())]
