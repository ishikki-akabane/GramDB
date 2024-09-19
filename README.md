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
from gramdb import GramDB, AsyncManager 

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
await gramdb.create_one("users", schema)
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
await gramdb.insert_one("users", record)
```
### Fetching Data
```python
# Define the query criteria
query = {
    "name": "John Doe"
}
    
# Fetch the data
result = await gramdb.find_one("users", query)
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
await gramdb.update_one("users", query, update_fields)
```
### Deleting Data
```python
# Define the query criteria
query = {
    "name": "John Doe"
}
    
# Delete the data
await gramdb.delete_one("users", query)
```

## Methods
### Authentication and Initialization
- `__init__(db_url, async_manager)`: Initialize the GramDB instance with the provided database URL and asynchronous manager.
- `authenticate()`: Authenticate with the provided database URL.
### Data Operations
- `create_one(table_name, schema)`: Create a new table with the given schema.
- `insert_one(table_name, record)`: Insert a new record into the specified table.
- `find(table_name, query)`: Fetch records from the specified table based on the given query.
- `find_one(table_name, query)`: Fetch one record from the specified table based on the given query.
- `fetch_all()`: Fetch all records from all tables.
- `update_one(table_name, query, update_query)`: Update records in the specified table based on the given query and update criteria.
- `delete_one(table_name, query)`: Delete records from the specified table based on the given query.
### Background Tasks
- `background_create(table_name, _m_id)`: Create a new table in the background.
- `background_insert(table_name, _m_id)`: Insert a new record in the background.
- `background_update(table_name, query, _m_id)`: Update records in the background.
- `background_delete(table_name, _m_id)`: Delete a record in the background.
- `background_delete_table(table_name)`: Delete a table in the background.
### Utility Methods
- `wait_for_background_tasks()`: Wait for all background tasks to complete.
- `close()`: Run async background tasks and close the async manager.

## API Documentation
For detailed API documentation, please refer to the API Documentation.
## Contributing
Contributions are welcome If you find any issues or have suggestions, please open an issue or submit a pull request.
## License
GramDB is licensed under the GPU License.


