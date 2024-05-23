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
    1112223334: {                # client id
        "bio_table": [5,87,65]   # table name : [msg ids] | table name : rows
    } 
}

CACHE_ROW_DICT = {
    5: [82938373, "I'm alpha male"] # msg id : [user id, bio msg]
}
#----------------------------------------------

async def append_table_value(data, list_key, value):
    final_str = ""
    key_found = False
    
    a = data.strip().split("\n")
    final_str = f"{a[0]}\n"
    for i in a:
        try:
            b = i.split(":")[0].split("-")[1]
            if list_key == b:
                key_found = True
                new_str = f"-{b}:"
                new_str += i.split(":")[1]
                new_str += f"{value},"
            else:
                if i != "":
                    final_str += f"\n{i}"
        except:
            pass
            
    if key_found == False:
        new_str = f"-{list_key}: {value},"
        
    final_str += f"\n{new_str}"
    return final_str


async def check_user_bio(user_id, table_name):
    all_rows = CACHE_TABLE_DICT[6969696969][table_name]
    for i in all_rows:
        if user_id in CACHE_ROW_DICT[i][0]:
            return CACHE_ROW_DICT[i][1], i
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
    else:
        reply_text = f"Your new bio **{bio_msg}** set successfully!!"
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
    response = await save_bio(client, unique_client_id, user_id, bio_msg, "bio_table")
    await message.reply_text(response)


@app.on_message(filters.command("bio"))
async def bio_watcher(client, message):
    user_id = message.from_user.id
    bio_msg = await get_bio(unique_client_id, user_id)
    await message.reply_text(bio_msg)
        

app.run()
