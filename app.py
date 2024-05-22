from pyrogram import Client, filters


api_id = 14681826
api_hash = 'add59ab14dbbccf3c92c65ca4477f2fa'

token = '6191819669:AAH-BrQM5FiaBSdZBOo8TaXv90GyO1rmljE'

app = Client("bluebot", api_id=api_id, api_hash=api_hash, bot_token=token)


db_channel = -1002091888299
admin_db = -1002095211836

db_dict = {
    6969696969: [4] # channel id : msg id for all tables info
}

unique_client_id = 6969696969


async def save_bio(client, client_id, user_id, bio_msg):
    db_text = f"{user_id}:{bio_msg}"
    msg = await client.send_message(
        db_channel,
        db_text
    )
    
    table_info = db_dict[client_id][0]
    msg_texts = await client.get_messages(admin_db, table_info)
    new_msg = f""
    await client.edit_message(
        
    )
    return


async def get_bio(unique_client_id, user_id)


@app.on_message(filters.command("setbio"))
async def setbio_message(client, message):
    user_id = message.from_user.id
    bio_msg = message.text.split(None, 1)[1]
    await save_bio(client, unique_client_id, user_id, bio_msg)
    await message.reply_text("bio set successfully!!")


@app.on_message(filters.command("bio"))
async def bio_watcher(client, message):
    user_id = message.from_user.id
    bio_msg = await get_bio(unique_client_id, user_id)
    await message.reply_text(bio_msg)
        

app.run()
