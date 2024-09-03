# yoii - ishikki - test

#from GramDB import GramDB
#import asyncio
#import json



CACHE_TABLE = {
  "info_gramdb": {
    "name": "ishikki", "password": "v_143", "telegram_id": 6282920
  },
  "bio_table": [21, 22]
}

CACHE_DATA = {
  '21': {'_m_id': '21', '_table_': 'bio_table', 'id': 1234567891, 'bio': "I'm alpha"},
  '22': {'_m_id': '22', '_table_': 'bio_table', 'id': 1234567892, 'bio': "I'm cat"}
}

sample_efficitiantdb = {
  'bio_table': {
    '1234567891': {
      '_id': 1234567891, '_m_id': '21', 'bio': "I'm alpha"
    },
    '1234567892': {
      '_id': 1234567892, '_m_id': '22', 'bio': "I'm cat"
    }
  }
}

"""
async def bb_test():
  db = GramDB("https://blue-api.vercel.app/database?client=ishikki@xyz242.gramdb")
  a = await db.fetch_all()
  print(json.dumps(a, indent=4))    
  print("------------------------")
  db.close()
  
  
async def aa_test():
  db = GramDB("https://blue-api.vercel.app/database?client=ishikki@xyz242.gramdb")
  
  a = await db.fetch_all()
  print(json.dumps(a, indent=4))    
  print("------------------------")
  
  
  b = await db.create("final_test_1", ("_id", "name", "level"))
  a = await db.fetch_all()
  print(json.dumps(a, indent=4))    
  print("------------------------")
  

  c = await db.insert("final_test_1", {"_id": 9999999999, "name": "ishikki", "level": 999})
  a = await db.fetch_all()
  print(json.dumps(a, indent=4))    
  print("------------------------")


  d = await db.update("final_test_1",  {"_id": 9999999999}, {"name": "ishikki_akabane", "level": 9999})
  a = await db.fetch_all()
  print(json.dumps(a, indent=4))    
  print("------------------------")

  f = await db.delete("final_test_1",  {"name": "ishikki_akabane"})
  a = await db.fetch_all()
  print(json.dumps(a, indent=4))    
  print("------------------------")
  

  g = await db.delete_table("final_test_1")
  a = await db.fetch_all()
  print(json.dumps(a, indent=4))    
  print("------------------------")
  
  db.close()
"""

from GramDB import GramDB
import asyncio
import time


class DATABASE:
    def __init__(self, uri):
        self.client = GramDB(uri)
        print("DATABASE Online")

    async def create(self, table, query):
        await self.client.create(table, query)
    async def insert(self, table, query):
        await self.client.insert(table, query)
    async def update(self, table, query, new_query):
        await self.client.update(table, query, new_query)
    async def fetch(self, table, query):
        await self.client.fetch(table, query)
    async def check_table(self, table):
        h = await self.client.check_table(table)
        return h
    



db = DATABASE("https://blue-api.vercel.app/database?client=ishikki@xyz242.gramdb")

async def boot():
    create_1_time = time.time()
    await db.create("testusers", ("_id", "upload", "batch"))
    create_1_end = time.time()
    execution_1_time_ms = (create_1_end - create_1_time) * 1000

    create_2_time = time.time()
    await db.create("testfilesh", ("_id", "message_id"))
    create_2_end = time.time()
    execution_2_time_ms = (create_2_end - create_2_time) * 1000
  
    create_3_time = time.time()
    await db.create("testbatch", ("_id", "channel_id", "message_id"))
    create_3_end = time.time()
    execution_3_time_ms = (create_3_end - create_3_time) * 1000

    create_txt = "\n\ncreate:"
    create_txt += f"\n1: {execution_1_time_ms} ms"
    create_txt += f"\n2: {execution_2_time_ms} ms"
    create_txt += f"\n3: {execution_3_time_ms} ms"
    print(create_txt)
    

    create_1_time = time.time()
    await db.insert("testusers", {"_id": 123456, "upload": 123, "batch": 123})
    create_1_end = time.time()
    execution_1_time_ms = (create_1_end - create_1_time) * 1000

    create_2_time = time.time()
    await db.insert("testfilesh", {"_id": 123456, "message_id": 123})
    create_2_end = time.time()
    execution_2_time_ms = (create_2_end - create_2_time) * 1000
  
    create_3_time = time.time()
    await db.insert("testbatch", {"_id": 123456, "channel_id": 123, "message_id": 123})
    create_3_end = time.time()
    execution_3_time_ms = (create_3_end - create_3_time) * 1000

    insert_txt = "\n\ninsert:"
    insert_txt += f"\n1: {execution_1_time_ms} ms"
    insert_txt += f"\n2: {execution_2_time_ms} ms"
    insert_txt += f"\n3: {execution_3_time_ms} ms"
    print(insert_txt)


    create_1_time = time.time()
    await db.update("testusers", {"_id": 123456} , {"batch": 456})
    create_1_end = time.time()
    execution_1_time_ms = (create_1_end - create_1_time) * 1000

    create_2_time = time.time()
    await db.update("testfilesh", {"_id": 123456} , {"message_id": 456})
    create_2_end = time.time()
    execution_2_time_ms = (create_2_end - create_2_time) * 1000
  
    create_3_time = time.time()
    await db.update("testbatch", {"_id": 123456} , {"channel_id": 456, "message_id": 456})
    create_3_end = time.time()
    execution_3_time_ms = (create_3_end - create_3_time) * 1000

    update_txt = "\n\nupdate:"
    update_txt += f"\n1: {execution_1_time_ms} ms"
    update_txt += f"\n2: {execution_2_time_ms} ms"
    update_txt += f"\n3: {execution_3_time_ms} ms"
    print(update_txt)
    

    create_1_time = time.time()
    await db.fetch("testusers", {"_id": 123456})
    create_1_end = time.time()
    execution_1_time_ms = (create_1_end - create_1_time) * 1000

    create_2_time = time.time()
    await db.fetch("testfilesh", {"message_id": 456})
    create_2_end = time.time()
    execution_2_time_ms = (create_2_end - create_2_time) * 1000
  
    create_3_time = time.time()
    await db.fetch("testbatch", {"_id": 123456, "channel_id": 456})
    create_3_end = time.time()
    execution_3_time_ms = (create_3_end - create_3_time) * 1000

    fetch_txt = "\n\nFetch:"
    fetch_txt += f"\n1: {execution_1_time_ms} ms"
    fetch_txt += f"\n2: {execution_2_time_ms} ms"
    fetch_txt += f"\n3: {execution_3_time_ms} ms"    
    print(fetch_txt)

    a = await db.check_table("hahaha")
    print(a)
  
    await asyncio.sleep(10)


asyncio.run(boot())
print("ending...")
