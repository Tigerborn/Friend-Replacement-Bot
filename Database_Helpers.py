#Database Helpers
import os
from typing import Optional
from dotenv import load_dotenv
import aiomysql
from datetime import datetime, timedelta

load_dotenv()

#Helpers
db_pool = None

CLAIM_AMOUNT = 100
COOLDOWN = timedelta(days=1)

def _fmt_duration(seconds: int) -> str:
    if seconds <= 0:
        return "0s"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h: return f"{h}h {m}m"
    if m: return f"{m}m {s}s"
    return f"{s}s"

async def init_db_pool():
    global db_pool
    # Initialize the MariaDB connection pool.
    db_pool = await aiomysql.create_pool(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        db=os.getenv("DB_NAME"),
        autocommit=False,               # explicit commits for safety
        minsize=1,
        maxsize=5,                      # tune as needed
        charset="utf8mb4"
    )
    print("✅ Database connection pool created!")

async def close_db_pool():
    #Close db_pool on shutdown
    global db_pool
    if db_pool:
        db_pool.close()
        await db_pool.wait_closed()

async def show_databases(db_pool) -> str:
    message = ""
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SHOW DATABASES;")
            dbs = await cur.fetchall()
            message += f"Databases:\n"
            for db in dbs:
                message += f"- {db[0]}\n"
    return message

async def show_tables(db_pool, db_name: Optional[str] = None) -> str:
    message = ""
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            if db_name:
                await cur.execute(f"USE `{db_name}`;")
            await cur.execute("SELECT DATABASE();")
            (current_db,) = await cur.fetchone()
            await cur.execute("SHOW TABLES;")
            tables = await cur.fetchall()
            message += f"Tables in current DB: {current_db or '(none selected)'} \n"
            rows = await cur.fetchall()
            if not rows:
                message += f"- (no tables)\n"
            else:
                for (tbl,) in rows:
                    message += f"- {tbl}\n"
    return message

async def daily_claim(db_pool, uid:int, username:str) -> str:
    #Will allow the users to claim 100 credits every 24 hours. Will update necessary tables and added new users to database
    message = ""
    async with db_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            try:
                await cur.execute("START TRANSACTION")

                # 0) Ensure rows exist; keep username fresh
                await cur.execute("""
                    INSERT INTO Users (id, username, dailys_claimed, updated_at)
                    VALUES (%s, %s, 0, NULL)
                    ON DUPLICATE KEY UPDATE username = VALUES(username)
                """, (uid, username))

                await cur.execute("""
                    INSERT INTO Bank (id, credits, tokens)
                    VALUES (%s, 0, 0)
                    ON DUPLICATE KEY UPDATE id = id
                """, (uid,))

                await cur.execute("""
                    INSERT INTO User_Statistics (id, money_earned, money_lost)
                    VALUES (%s, 0, 0)
                    ON DUPLICATE KEY UPDATE id = id
                """, (uid,))

                # 1) Try to claim (cooldown enforced atomically in WHERE)
                await cur.execute("""
                    UPDATE Users
                    SET dailys_claimed = dailys_claimed + 1,
                        updated_at = NOW()
                    WHERE id = %s
                      AND (updated_at IS NULL OR updated_at <= NOW() - INTERVAL 1 DAY)
                """, (uid,))

                if cur.rowcount == 0:
                    # Not eligible yet; compute time remaining
                    await cur.execute("SELECT updated_at FROM Users WHERE id = %s", (uid,))
                    row = await cur.fetchone()
                    # Safety if NULL somehow
                    if not row or row["updated_at"] is None:
                        await conn.rollback()
                        return "Daily claim not available yet. Try again soon."

                    now = datetime.utcnow()
                    next_time = row["updated_at"] + COOLDOWN
                    seconds_left = max(int((next_time - now).total_seconds()), 0)
                    await conn.rollback()
                    return f"Daily Credits already claimed. Try again in {_fmt_duration(seconds_left)}."

                # 2) Apply credit and stats
                await cur.execute("UPDATE Bank SET credits = credits + %s WHERE id = %s",
                                  (CLAIM_AMOUNT, uid))
                await cur.execute("UPDATE User_Statistics SET money_earned = money_earned + %s WHERE id = %s",
                                  (CLAIM_AMOUNT, uid))

                # 3) Commit and fetch new balance for the message
                await conn.commit()

                await cur.execute("SELECT credits FROM Bank WHERE id = %s", (uid,))
                bank = await cur.fetchone()
                credits = bank["credits"] if bank else None

                return f"Daily Claimed: you gained {CLAIM_AMOUNT} credits.\nYour total balance is: {credits}"

            except Exception:
                await conn.rollback()
                raise


async def fortnite_daily_shop_cache(db_pool, date):
    async with db_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            try:
                await cur.execute("START TRANSACTION")
                #0) Ensure Row exist




            except Exception:
                await conn.rollback()
                raise








