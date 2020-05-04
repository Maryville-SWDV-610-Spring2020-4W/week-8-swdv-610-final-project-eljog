# Graph database and COVID contact tracing
## The Graph DB

This project first implements a [Graph Database](https://en.wikipedia.org/wiki/Graph_database) system in python, which anybody can use to store, update, retrieve, filter, and more importantly traverse through connected nodes. This can be used for building any app where the data is highly networked (such as Social networking system). The  graphdb comes with a custom query language. The syntax for interacting with the graphdb is documented below. Details can also be found in the code doc comments.
This is a high-performance, fully-indexed, in-memory graph database system. It provides constant time searching for data by any criteria. This is achieved using a full indexing strategy.

## The COVID contact tracing app
The second part of this project is an implementation of a Covid 19 contact tracing application based on this graph database system. The app uses graphdb as its backend and performs covid contact tracing and impact detection. This app can help authorities to understand possibly impacted set of people when a positive case is reported. This app can also be extended for more scenarios like finding the origin of a case. GraphDB is providing all the necessary APIs for searching, traversing, and filtering the data.
Below is the custom query language syntax for interacting with the DB.

## Query language Syntax for the Graph DB
`g = GraphDB()`

### Query Students by course
```Student:course=SW610```
```
g.query("Student:course=SW610")
```
 
### Query Student by Id
`Student:idvalue`
```
g.queryById("Student:idvalue")
```
 
### Query All Students
`Student` 
```
g.query("Student")
```
 
### Query all types of Nodes
```
g.query()
```
 
### Graph Query
Query the graph starting a Student with id "abc":
```
graphQuery("Student:abc")
```
 
### Graph Query with depth limit
Query the graph starting a Student with id "abc" and return only upto 10 levels of connections:
```
graphQuery("Student:abc", maxDepth=10)
```

### Graph Query with filter
Query the graph starting a Student with id "abc" and return only upto 10 levels of connections, and filter connections by course SW600:
```
q.graphQuery("Student:abc", "course=SW600", 10)
```
 
### Add a node
Add a node of type (label) Student with id ‘abc’.
```
g.addNode(‘Student’, 'abc')
```

### Add or update property.
Add the property ‘name’ for the student.
```
g.addOrUpdateNodeProperty(‘Student:abc, 'name', 'Eljo George')
```
Add the property ‘course’ for the student.
```
g.addOrUpdateNodeProperty(‘Student:abc, 'course', 'SW610')
```
