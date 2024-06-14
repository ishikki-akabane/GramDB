from pyrogram import Client, filters
from GramDB import GramDB
import asyncio


api_id = 14681826
api_hash = 'add59ab14dbbccf3c92c65ca4477f2fa'

token = '6191819669:AAH-BrQM5FiaBSdZBOo8TaXv90GyO1rmljE'

db = GramDB("https://blue-api.vercel.app/database?client=ishikki@xyz242.gramdb")

app = Client("bluebot", api_id=api_id, api_hash=api_hash, bot_token=token)

#----------------------------------------------

try:
    db.create("blue_db", ("_id", "name", "bio"))
except:
    pass


@app.on_message(filters.command("setbio"))
async def setbio_message(client, message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    bio_msg = message.text.split(None, 1)[1]
    response = await db.insert("blue_db", {"_id": user_id, "name": name, "bio": bio_msg})
    await message.reply_text("Bio set successfully")


@app.on_message(filters.command("bio"))
async def bio_watcher(client, message):
    user_id = message.from_user.id
    bio_msg = await db.fetch("blue_db", {"_id": user_id})
    if bio_msg:
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
