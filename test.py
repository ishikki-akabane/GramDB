# yoii - ishikki

from GramDB import GramDB

db = GramDB("https://blue-api.vercel.app/database?client=ishikki@xyz242.gramdb")

print(db.CACHE_TABLE)
db.close()
print("ending...")
