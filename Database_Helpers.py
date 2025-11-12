#Database Helpers
import os
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

async def close_db_pool():
    #Close db_pool on shutdown
    global db_pool
    if db_pool:
        db_pool.close()
        await db_pool.wait_closed()

async def show_databases():
    message = ""
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SHOW DATABASES;")
            dbs = await cur.fetchall()
            message += f"Databases:\n"
            for db in dbs:
                message += f"- {db[0]}\n"

async def show_tables():
    message = ""
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SHOW TABLES;")
            tables = await cur.fetchall()
            message += f"Tables in current DB: \n"
            for t in tables:
                message += f"- {t[0]}\n"