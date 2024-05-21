from pyrogram import Client, filters


api_id = 14681826
api_hash = 'add59ab14dbbccf3c92c65ca4477f2fa'

token = '6191819669:AAH-BrQM5FiaBSdZBOo8TaXv90GyO1rmljE'

app = Client("bluebot", api_id=api_id, api_hash=api_hash, bot_token=token)


@app.on_message(filters.command("ffilter"))
async def filter_message(client, message):
    filter_msg = message.text.split(None, 1)[1]
    save_filter()
    await message.reply_text("filter set successfully!!")



app.run()
