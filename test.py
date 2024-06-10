# yoii - ishikki

from GramDB import GramDB
import asyncio


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


async def aa():
  db = GramDB("https://blue-api.vercel.app/database?client=ishikki@xyz242.gramdb")

  lines = []
  while True:
    line = input()
    if line == "":
      break
    lines.append(line)
    command = "\n".join(lines)
            
    if command.strip() == "end":
      break     
        
    local_vars = {"db": db, "asyncio": asyncio}

    exec(f"async def __user_code__():\n" + "\n".join(f"    {line}" for line in command.split("\n")), local_vars)
            
    result = await local_vars["__user_code__"]()
    if result:
      print(result)
    else:
      print("None")
  db.close()
    
asyncio.run(aa())

print("ending...")
