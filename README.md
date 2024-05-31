# GramDB


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


### Insert
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
