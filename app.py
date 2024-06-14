from pyrogram import Client, filters
from GramDB import GramDB
import asyncio
import time
from pymongo import MongoClient


api_id = 14681826
api_hash = 'add59ab14dbbccf3c92c65ca4477f2fa'

token = '6191819669:AAH-BrQM5FiaBSdZBOo8TaXv90GyO1rmljE'

db = GramDB("https://blue-api.vercel.app/database?client=ishikki@xyz242.gramdb")

url = "mongodb+srv://botmaker9675208:botmaker9675208@cluster0.sc9mq8b.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
c = MongoClient(url)
mdb = c["test"]["test"]

app = Client("bluebot", api_id=api_id, api_hash=api_hash, bot_token=token)

#----------------------------------------------

@app.on_message(filters.command("test"))
async def testt(client, message):
    f_text = "Speed test ⚡\n"
    await message.reply_text("running speedtest...")
    
    start_time1 = time.time()
    a = mdb.insert_one({"_id": 987654321, "name": "rohan", "bio": "haha"})
    end_time1 = time.time()
    start_time2 = time.time()
    b = await db.insert("blue_db", {"_id": 987654321, "name": "rohan", "bio": "haha"})
    end_time2 = time.time()
    f_text += f"\n• Insert\n- {end_time1 - start_time1}\n- {end_time2 - start_time2}\n"


    start_time3 = time.time()
    a = mdb.update_one({"_id": 987654321}, {"$set": {"bio": "hahaha"}})
    end_time3 = time.time()
    start_time4 = time.time()
    b = await db.update("blue_db", {"_id": 987654321}, {"bio": "hahaha"})
    end_time4 = time.time()
    f_text += f"\n• Update\n- {end_time3 - start_time3}\n- {end_time4 - start_time4}\n"


    start_time5 = time.time()
    a = mdb.find_one({"_id": 987654321})
    end_time5 = time.time()
    start_time6 = time.time()
    b = await db.fetch("blue_db", {"_id": 987654321})
    end_time6 = time.time()
    f_text += f"\n• Fetch\n- {end_time5 - start_time5}\n- {end_time6 - start_time6}\n"

    await message.reply_text(f_text)
    
    


@app.on_message(filters.command("set"))
async def setbio_message(client, message):
    user_id = message.from_user.id
    bio_msg = message.text.split(None, 1)[1]
    data = await db.fetch("blue_db", {"_id": user_id})
    if data:
        old_bio = data["bio"]
        await db.update("blue_db", {"_id": user_id}, {"bio": bio_msg})
        await message.reply_text(f"Your bio changed from {old_bio} to {bio_msg}")
        return
        
    name = message.from_user.first_name
    response = await db.insert("blue_db", {"_id": user_id, "name": name, "bio": bio_msg})
    await message.reply_text("Bio set successfully")


@app.on_message(filters.command("bio"))
async def bio_watcher(client, message):
    user_id = message.from_user.id
    bio_data = await db.fetch("blue_db", {"_id": user_id})
    if bio_data:
        bio_msg = bio_data["bio"]
        await message.reply_text(f"Your bio: `{bio_msg}`")
    else:
        await message.reply_text("You haven't set any bio yet!!")


@app.on_message(filters.command("allbio"))
async def allbio_watcher(client, message):
    user_id = message.from_user.id
    data_list = await db.fetch_all()
    bio_list = data_list["blue_db"]
    ftext = "all saved bio:\n"
    for i, j in bio_list.items():
        name = j["name"]
        bioo = j["bio"]
        ftext += f"\n• {name}: {bioo}"
    await message.reply_text(ftext)


    
print("started...")
app.run()
