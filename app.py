from pyrogram import Client, filters


api_id = 14681826
api_hash = 'add59ab14dbbccf3c92c65ca4477f2fa'

token = '6191819669:AAH-BrQM5FiaBSdZBOo8TaXv90GyO1rmljE'

app = Client("bluebot", api_id=api_id, api_hash=api_hash, bot_token=token)


#----------------------------------------------


@app.on_message(filters.command("setbio"))
async def setbio_message(client, message):
    user_id = message.from_user.id
    bio_msg = message.text.split(None, 1)[1]
    response = await save_bio(client, unique_client_id, user_id, bio_msg, "bio_table")
    await message.reply_text(response)


@app.on_message(filters.command("bio"))
async def bio_watcher(client, message):
    user_id = message.from_user.id
    bio_msg = await get_bio(unique_client_id, user_id, "bio_table")
    await message.reply_text(bio_msg)


@app.on_message(filters.command("allbio"))
async def allbio_watcher(client, message):
    user_id = message.from_user.id
    bio_msg = await get_bio(unique_client_id, user_id, "bio_table")
    await message.reply_text(bio_msg)


print("started...")
app.run()
