# GramDB


### Data format:
```
{
    "_id": 6939393728, # primary key
    "_m_id": "54", # data id
    "name": "ishikki",
    ... so on in json format
}
```
- Primary key is a mandatory key which will exist in all records.
- "_id" key represents the primary key
- If no primary key provided while inserting record, random unique primary key will be generated and will get inserted with the record
- Data id represents the location of data
- "_m_id" key represents the data id
- It's a reserved key which gets generated automatically
