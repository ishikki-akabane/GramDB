# yoii - ishikki

from GramDB import GramDB
import asyncio
import json


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


asyncio.run(aa_test())

print("ending...")
