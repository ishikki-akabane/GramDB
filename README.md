# GramDB: Infinite Database Storage via Telegram
=====================================================

## Introduction
GramDB is a unique library that leverages Telegram as a database, offering infinite storage capabilities. It provides a robust and efficient way to manage data, making it an ideal solution for applications requiring flexible and scalable data storage.

## Features
- **Infinite Storage**: Utilize Telegram's messaging capabilities to store data without traditional storage limitations.
- **Real-time Data Access**: Fetch, insert, update, and delete data in real-time.
- **Asynchronous Operations**: Support for asynchronous operations to ensure non-blocking and efficient data management.
- **Schema Management**: Define and manage schemas for tables to ensure data consistency.
- **Background Tasks**: Handle background tasks for creating, updating, and deleting data seamlessly.

## Installation
To use GramDB, you need to install the library and its dependencies. You can do this via pip:

```bash
pip install gramdb
```

## Getting Started
1. **Authentication**: Authenticate with your Telegram database URL.
2. **Initialize**: Initialize the GramDB instance with the authenticated URL and an asynchronous manager.
3. **Data Operations**: Perform CRUD (Create, Read, Update, Delete) operations on your data.

## Example Usage
### Authentication and Initialization
```python
from gramdb import GramDB
from gramdb.asyncio import AsyncManager

# Replace with your actual database URL
db_url = "https://your-telegram-db-url.com"

# Initialize the asynchronous manager
async_manager = AsyncManager()

# Initialize GramDB
gramdb = GramDB(db_url, async_manager)
```
### Creating a Table
```python
# Define the schema for the new table
schema = ["name", "age", "email"]
    
# Create the table
await gramdb.create("users", schema)
```
### Inserting Data
```python
# Define the record to insert
record = {
    "name": "John Doe",
    "age": 30,
    "email": "john.doe@example.com"
}
    
# Insert the record
await gramdb.insert("users", record)
```
### Fetching Data
```python
# Define the query criteria
query = {
    "name": "John Doe"
}
    
# Fetch the data
result = await gramdb.fetch("users", query)
print(result)
```
### Updating Data
```python
# Define the query criteria and update fields
query = {
    "name": "John Doe"
}
update_fields = {
    "$set": {
        "age": 31
    }
}
    
# Update the data
await gramdb.update("users", query, update_fields)
```
### Deleting Data
```python
# Define the query criteria
query = {
    "name": "John Doe"
}
    
# Delete the data
await gramdb.delete("users", query)
```





## Data Structure:

- ### GramDB Class:
- `CACHE_TABLE`: Dictionary containing table names as keys and a list of record IDs as values.
```
{"test_table": [123, 456]}
```

- `CACHE_DATA`: Dictionary containing all records with their record ID key (`_m_id`) as keys and the record data as values.
```
{"123": {"_m_id": "123", "_id": 696969696969, "name": "John", "age": 30}}
```

- `db`: Instance of `EfficientDictQuery` class which holds the actual in-memory data structure for efficient querying.


- ### EfficientDictQuery Class:
- `data`: Dictionary containing tables as keys and dictionaries of records as values. Each record dictionary has its primary key (`_id`) as a key and the record data as the value. (Similar to `CACHE_DATA` but potentially more organized)
```
{"696969696969": {"_id": "696969696969", "_m_id": "123", "name": "John", "age": 30}}
```

- `indexes`: Dictionary where each key represents a field name in the records, and the value is another dictionary. This inner dictionary maps each unique value of that field to a list of (table_name, record_id) tuples referencing records containing that value.
- `schemas`: Dictionary containing table names as keys and tuples of field names (schema) as values.


## Functionalities:

- ### GramDB Class:
- `initialize()`: Initializes the connection with the Telegram database by fetching authentication details and building the internal data structures.
- `create(table_name, schema)`: Creates a new table with the specified schema (list of field names).
- `fetch(table_name, query)`: Fetches records from a table based on a query dictionary (key-value pairs matching record fields).
- `fetch_all()`: Fetches all records from all tables.
- `insert(table_name, record)`: Inserts a new record into a table. The record must contain a `_id` field.
- `delete(table_name, query)`: Deletes records from a table based on a query dictionary.
- `update(table_name, query, update_query)`: Updates records in a table based on a query dictionary and updates the specified fields with the values provided in the `update_query` dictionary.
- `delete_table(table_name)`: Deletes a table entirely.
- `close()`: Closes the asynchronous session.


- ### EfficientDictQuery Class:
- Provides methods for querying, inserting, updating, and deleting data efficiently using the internal data structures (`data`, `indexes`, and `schemas`).
Maintains indexes to enable faster searches based on field values.



## Data format:
- ### CACHE_TABLE
```
{
    "_id": 6939393728, # primary key
    "_m_id": "54", # data id
    "name": "akabane",
    ... so on in json format
}
```
- **PRIMARY KEY**
  - Primary key is a mandatory key which will exist in all records.
  - "_id" key represents the primary key
  - If no primary key provided while inserting record, random unique primary key will be generated and will get inserted with the record
  - It is unique for every record

- **DATA KEY**
  - Data id represents the location of data
  - "_m_id" key represents the data id
  - It's a reserved key which gets generated automatically
  - It is unique for every record


### create
```
await db.create("table_name", ("name", "rollno", "section"))
```
- table_name: name of the table that you want to create
- schema: set of fields


### fetch_all
```
result = await db.fetch_all()
```
- returns all records in list


### fetch
```
result = await db.fetch("table_name", {"name": "akabane"})
```
- table_name: name of the table
- query: your search query
- returns specific records matching the query


### insert
```
data = {
    "name": "akabane",
    "class": 3,
    "rollno": 24
}

await db.insert("table_name", data)
```
- table_name: name of the table
- record: your data in JSON/dict form


### delete
```
await db.delete("table_name", {"name": "akabane"})
```
- table_name: name of the table
- query: query for deleting matching data


### delete_table
```
await db.delete_table("table_name)
```
- table_name: name of the table


### update
```
query = {
    "name": "akabane"
}

update_query = {
    "class": 7
}

await db.update("table_name", query, update_query)
```
- table_name: name of the table
- query: query for deleting matching data
- update_query: data for inserting new data 


