# yoii - ishikki

from GramDB import GramDB

CACHE_TABLE = {
  "info_gramdb": {
    "name": "ishikki", "password": "v_143", "telegram_id": 6282920
  },
  "test_table": [20],
  "bio_table": [21, 22]
}

CACHE_DATA = {
  '20': {'_m_id': '20', '_table_': 'test_table', 'username': 'ishikki_akabane', 'bio': "I'm natsu dragneel"},
  '21': {'_m_id': '21', '_table_': 'bio_table', 'id': 1234567891, 'bio': "I'm alpha"},
  '22': {'_m_id': '22', '_table_': 'bio_table', 'id': 1234567892, 'bio': "I'm cat"}
}



db = GramDB("https://blue-api.vercel.app/database?client=ishikki@xyz242.gramdb")

db.close()
print("ending...")
