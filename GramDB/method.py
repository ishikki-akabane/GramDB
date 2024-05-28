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


async def insert_func(session, base_url, token, data):
    url = base_url + "/insert"
    headers = {
        "Content-Type": "application/json",
        "Authorization": token
    }
    payload = {
        "data": data
    }

    response = await session.post(url, headers=headers, json=payload)
    if response.status == 200:
        result = await response.json()
        return True, result
    else:
        return False, response.status
