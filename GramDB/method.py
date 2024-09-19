import requests
import json
import copy
import aiohttp

# Methods

async def fetch_func(session, base_url, token, data_id):
    """
    Fetch data from the server based on the provided data ID.

    :param session: The aiohttp session object.
    :param base_url: The base URL of the server.
    :param token: The authorization token.
    :param data_id: The ID of the data to fetch.
    :return: A tuple containing a boolean indicating success and the response data.
    """
    url = f"{base_url}/fetch"
    headers = {
        "Content-Type": "application/json",
        "Authorization": token
    }
    payload = {"data_id": data_id}
    async with session.post(url, headers=headers, json=payload) as response:
        if response.status == 200:
            return True, await response.json()
        else:
            return False, response.status

async def insert_func(session, base_url, token, data, table_name):
    """
    Insert new data into the server.

    :param session: The aiohttp session object.
    :param base_url: The base URL of the server.
    :param token: The authorization token.
    :param data: The data to insert.
    :param table_name: The name of the table to insert into.
    :return: A tuple containing a boolean indicating success and the response data.
    """
    url = f"{base_url}/insert"
    headers = {
        "Content-Type": "application/json",
        "Authorization": token
    }
    data["_table_"] = table_name
    print(data)
    try:
        payload = {"data": json.dumps(data)}
    except:
        return False, "wrong data format for json"
        
    async with session.post(url, headers=headers, json=payload) as response:
        try:
            jdata = await response.json()
        except:
            jdata = response.text
        if response.status == 201:
            return True, jdata
        else:
            return False, jdata

async def delete_func(session, base_url, token, data_id):
    """
    Delete data from the server based on the provided data ID.

    :param session: The aiohttp session object.
    :param base_url: The base URL of the server.
    :param token: The authorization token.
    :param data_id: The ID of the data to delete.
    :return: A tuple containing a boolean indicating success and the response data.
    """
    url = f"{base_url}/delete"
    headers = {
        "Content-Type": "application/json",
        "Authorization": token
    }
    payload = {"data_id": data_id}
    async with session.post(url, headers=headers, json=payload) as response:
        if response.status == 200:
            return True, await response.json()
        else:
            return False, response.status

async def update_func(session, base_url, token, data_id, data, table_name):
    """
    Update existing data in the server.

    :param session: The aiohttp session object.
    :param base_url: The base URL of the server.
    :param token: The authorization token.
    :param data_id: The ID of the data to update.
    :param data: The updated data.
    :param table_name: The name of the table to update.
    :return: A tuple containing a boolean indicating success and the response data.
    """
    url = f"{base_url}/update"
    headers = {
        "Content-Type": "application/json",
        "Authorization": token
    }
    data_copy = copy.deepcopy(data)
    data_copy["_table_"] = table_name
    del data_copy["_m_id"]
    payload = {"data_id": data_id, "data": json.dumps(data_copy)}
    async with session.post(url, headers=headers, json=payload) as response:
        if response.status == 200:
            return True, await response.json()
        else:
            return False, response.status

async def git_func(session, base_url, token, data):
    """
    Perform a Git operation on the server.

    :param session: The aiohttp session object.
    :param base_url: The base URL of the server.
    :param token: The authorization token.
    :param data: The data for the Git operation.
    :return: A tuple containing a boolean indicating success and the response data.
    """
    url = f"{base_url}/git"
    headers = {
        "Content-Type": "application/json",
        "Authorization": token
    }
    payload = {"data": data}
    async with session.post(url, headers=headers, json=payload) as response:
        if response.status == 200:
            return True, await response.json()
        else:
            return False, response.status

def extract_func(base_url, token):
    """
    Extract data from the server.

    :param base_url: The base URL of the server.
    :param token: The authorization token.
    :return: A tuple containing a boolean indicating success and the response data.
    """
    url = f"{base_url}/extract?token={token}"
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return True, response.json()
    else:
        return False, response.status_code

async def async_extract_func(base_url, token):
    """
    Asynchronously extract data from the server.

    **Note:** This method is redundant and can be replaced with `extract_func` since it does not use asynchronous requests.

    :param base_url: The base URL of the server.
    :param token: The authorization token.
    :return: A tuple containing a boolean indicating success and the response data.
    """
    # This method is redundant and can be replaced with extract_func
    return extract_func(base_url, token)

def fetchall_func(base_url, token, data_ids):
    """
    Fetch all data from the server based on the provided data IDs.

    :param base_url: The base URL of the server.
    :param token: The authorization token.
    :param data_ids: A list of data IDs to fetch.
    :return: A tuple containing a boolean indicating success and the response data.
    """
    url = f"{base_url}/fetchall"
    headers = {
        "Content-Type": "application/json",
        "Authorization": token
    }
    payload = {"data_id": data_ids}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return True, response.json()
    else:
        return False, response.status_code

