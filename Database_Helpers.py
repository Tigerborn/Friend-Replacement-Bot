#Database Helpers
import os
from typing import Optional
from dotenv import load_dotenv
import aiomysql

load_dotenv()

#Helpers
db_pool = None

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