from pyrogram import Client, filters
import json

api_id = 14681826
api_hash = 'add59ab14dbbccf3c92c65ca4477f2fa'

token = '6191819669:AAH-BrQM5FiaBSdZBOo8TaXv90GyO1rmljE'

app = Client("bluebot", api_id=api_id, api_hash=api_hash, bot_token=token)


db_channel = -1002091888299
admin_db = -1002095211836

unique_client_id = 6969696969


#----------------------------------------------
CACHE_TABLE_DICT = {
    6969696969: {             # client id
        "bio_table": [7]      # table name : [msg ids] | table name : rows
    }
}

CACHE_ROW_DICT = {
    7: [5030730429, "I'm ishikki"] # msg id : [user id, bio msg]
}
#----------------------------------------------


async def check_user_bio(user_id, table_name):
    all_rows = CACHE_TABLE_DICT[6969696969][table_name]
    for i in all_rows:
        dict_data = CACHE_ROW_DICT[i]
        if user_id in dict_data[0]:
            return dict_data[1], i
    return None, None

async def save_bio(client, client_id, user_id, bio_msg, table_name):
    db_text = f"[{user_id}, {bio_msg}]"
    
    result, msg_id = await check_user_bio(user_id, table_name)    
    if result:
        reply_text = f"Your bio has been updated from **{result}** to **{bio_msg}**"
        msg = await client.edit_message_text(
            db_channel,
            msg_id,
            db_text
        )
        CACHE_ROW_DICT[msg_id] = [user_id, bio_msg]
    else:
        reply_text = f"Your new bio **{bio_msg}** set successfully!!"
        msg = await client.send_message(
            db_channel,
            db_text
        )
        CACHE_ROW_DICT[msg.id] = [user_id, bio_msg]
        msg_list = CACHE_TABLE_DICT[client_id][table_name]
        msg_list.append(msg.id)
        
    return reply_text


async def get_bio(unique_client_id, user_id, table_name):
    result, msg_id = await check_user_bio(user_id, table_name)
    if result:
        return result
    else:
        return "Null"


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
        
print("started...")
app.run()
