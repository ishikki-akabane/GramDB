# methods
import requests


async def fetch_func(session, base_url, token, data_id):
    url = base_url + "/fetch"
    headers = {
        "Content-Type": "application/json",
        "Authorization": token
    }
    payload = {
        "data_id": data_id
    }
    response = await session.post(url, headers=headers, json=payload)
    if response.status == 200:
        result = await response.json()
        return True, result
    else:
        return False, response.status


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


async def delete_func(session, base_url, token, data_id):
    url = base_url + "/delete"
    headers = {
        "Content-Type": "application/json",
        "Authorization": token
    }
    payload = {
        "data_id": data_id
    }
    response = await session.post(url, headers=headers, json=payload)
    if response.status == 200:
        result = await response.json()
        return True, result
    else:
        return False, response.status


async def update_func(session, base_url, token, data_id, data):
    url = base_url + "/update"
    headers = {
        "Content-Type": "application/json",
        "Authorization": token
    }
    payload = {
        "data_id": data_id,
        "data": data
    }
    response = await session.post(url, headers=headers, json=payload)
    if response.status == 200:
        result = await response.json()
        return True, result
    else:
        return False, response.status


async def git_func(session, base_url, token, data):
    url = base_url + "/git"
    headers = {
        "Content-Type": "application/json",
        "Authorization": token
    }
    payload = {
        "data" : data
    }
    response = await session.post(url, headers=headers, json=payload)
    if response.status == 200:
        result = await response.json()
        return True, result
    else:
        return False, response.status


def extract_func(base_url, token):
    url = base_url + f"/extract?token={token}"
    headers = {
        "Content-Type": "application/json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        result = response.json()
        return True, result
    else:
        return False, response.status_code
    

def fetchall_func(base_url, token, data_ids):
    url = base_url + "/fetchall"
    headers = {
        "Content-Type": "application/json",
        "Authorization": token
    }
    payload = {
        "data_id": data_ids
    }
    response = await requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        result = await response.json()
        return True, result
    else:
        return False, response.status_code
        
