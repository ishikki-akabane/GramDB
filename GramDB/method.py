# methods

async def fetch_func(session, base_url, token, data_id):
    url = base_url + "/fetch"
    params = {
        "token": token,
        "data_id": data_id
    }

    response = await session.get(url, params=params)
    if response.status == 200:
        result = await response.json()
    else:
        result = False
