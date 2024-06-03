# GramDB


## Data Structure:

### GramDB Class:
- `CACHE_TABLE`: Dictionary containing table names as keys and a list of record IDs (primary keys) as values. (e.g., {"test_table": ["123", "456"]})
- `CACHE_DATA`: Dictionary containing all records with their primary key (_id) as keys and the record data as values. (e.g., {"123": {"name": "John", "age": 30}, "456": {"name": "Jane", "city": "New York"}})
- `db`: Instance of EfficientDictQuery class which holds the actual in-memory data structure for efficient querying.


### EfficientDictQuery Class:
- `data`: Dictionary containing tables as keys and dictionaries of records as values. Each record dictionary has its primary key (_id) as a key and the record data as the value. (Similar to CACHE_DATA but potentially more organized)
- `indexes`: Dictionary where each key represents a field name in the records, and the value is another dictionary. This inner dictionary maps each unique value of that field to a list of (table_name, record_id) tuples referencing records containing that value.
- `schemas`: Dictionary containing table names as keys and tuples of field names (schema) as values.

### Data format:
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


