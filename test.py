import asyncio
import logging
import os
import statistics
import time
import uuid

import aiohttp
from dotenv import load_dotenv

from GramDB import GramDB
from GramDB.config import parse_database_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("GramDB-Test")

# --- CONFIGURATION ---
# Replace these with your live credentials or set them in environment variables
load_dotenv()

DATABASE_URL = os.getenv(
    "GRAMDB_URL",
    "http://localhost:8080/api/v1/metadata?client=test"
)
BOT_TOKENS = os.getenv("BOT_TOKENS", "TOKEN1").split(",")
API_ID = os.getenv("API_ID", 123456789)
API_HASH = os.getenv("API_HASH", "111222333aaabbbccddd")


def _ms(t0: float, t1: float) -> float:
    return (t1 - t0) * 1000.0


async def _timed(label: str, coro):  # noqa: ANN001
    t0 = time.perf_counter()
    out = await coro
    t1 = time.perf_counter()
    logger.info("%s: %.2f ms", label, _ms(t0, t1))
    return out


async def _benchmark_find_one(db: GramDB, table_name: str, record_id: str, *, rounds: int) -> None:
    durs: list[float] = []
    for _ in range(rounds):
        t0 = time.perf_counter()
        await db.find_one(table_name, {"_id": record_id})
        durs.append(_ms(t0, time.perf_counter()))

    durs.sort()
    avg = statistics.fmean(durs) if durs else 0.0
    p50 = durs[int(0.50 * (len(durs) - 1))] if durs else 0.0
    p95 = durs[int(0.95 * (len(durs) - 1))] if durs else 0.0
    logger.info("Algorithm benchmark (find_one x%d): avg=%.3f ms p50=%.3f ms p95=%.3f ms", rounds, avg, p50, p95)


async def _benchmark_registry_metadata(url: str, *, rounds: int) -> dict:
    durs: list[float] = []
    last: dict = {}
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        for _ in range(rounds):
            t0 = time.perf_counter()
            async with s.get(url) as resp:
                data = await resp.json(content_type=None)
            durs.append(_ms(t0, time.perf_counter()))
            if isinstance(data, dict):
                last = data

    durs.sort()
    avg = statistics.fmean(durs) if durs else 0.0
    p50 = durs[int(0.50 * (len(durs) - 1))] if durs else 0.0
    p95 = durs[int(0.95 * (len(durs) - 1))] if durs else 0.0
    logger.info("API benchmark (GET /metadata x%d): avg=%.2f ms p50=%.2f ms p95=%.2f ms", rounds, avg, p50, p95)
    return last


async def run_crud_test():
    """
    Performs a custom cycle on GramDB to view tables, check for 'ishikki' table,
    create it if not present, populate it with disha (id: 111222333),
    show the table, update it to bella, and show it again.
    """
    logger.info("Starting GramDB custom user test...")

    db = GramDB(DATABASE_URL, BOT_TOKENS, int(API_ID), str(API_HASH))
    t0 = time.perf_counter()
    await db.connect(client_label="user-custom-test")
    logger.info("GramDB connect (total): %.2f ms", _ms(t0, time.perf_counter()))
    try:
        # 1. See how many tables are there and show that tables' data
        all_data = await db.find_all()
        tables = list(all_data.keys())
        print("\n" + "="*50)
        print(f"DATABASE METADATA: Found {len(tables)} tables.")
        print(f"Tables list: {tables}")
        print("="*50)
        
        print("\n--- INITIAL TABLES DATA ---")
        for t in tables:
            print(f"Table '{t}':")
            records = list(all_data[t].values())
            if not records:
                print("  (empty table)")
            for rec in records:
                print(f"  - {rec}")
        print("-"*50)

        # To demonstrate the 'if not' creation flow cleanly,
        # if 'ishikki' already exists, we delete it first.
        target_table = "ishikki"
        if target_table in tables:
            print(f"\nTable '{target_table}' already exists. Deleting it to demonstrate the creation flow from scratch...")
            await db.delete_table(target_table)
            # Re-fetch the updated state
            all_data = await db.find_all()
            tables = list(all_data.keys())

        # 2. "if not, create a table name ishikki, save name as disha and user id be 111222333. then show the table data."
        if target_table not in tables:
            print(f"\nTable '{target_table}' not found (as expected). Creating table '{target_table}'...")
            schema = ("name", "user_id")
            await db.create_one(target_table, schema)
            print(f"Table '{target_table}' created successfully.")

            print(f"\nSaving record to '{target_table}': name='disha', user_id=111222333...")
            record = {
                "_id": "111222333",
                "name": "disha",
                "user_id": 111222333
            }
            await db.insert_one(target_table, record)
            print("Record saved.")

            # Show the table data
            print(f"\n--- '{target_table}' TABLE DATA ---")
            updated_data = await db.find_all()
            for rid, rec in updated_data.get(target_table, {}).items():
                print(f"  - {rec}")
            print("-"*50)

            # 3. "Then edit the name to bella. then again show the table"
            print(f"\nEditing name in '{target_table}' to 'bella'...")
            await db.update_one(
                target_table,
                {"_id": "111222333"},
                {"$set": {"name": "bella"}}
            )
            print("Record updated.")

            # Show the table data again
            print(f"\n--- '{target_table}' TABLE DATA AFTER EDIT ---")
            updated_data2 = await db.find_all()
            for rid, rec in updated_data2.get(target_table, {}).items():
                print(f"  - {rec}")
            print("="*50)

    finally:
        await db.close()

    logger.info("GramDB test completed successfully.")

if __name__ == "__main__":
    try:
        asyncio.run(run_crud_test())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(f"Test failed with error: {e}")
