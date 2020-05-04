'''
A high-performance, fully-indexed, in-memory graph database system.
'''


class Node:
    '''
    Represents a node in the graph database.
    '''

    def __init__(self, id, label='Node'):
        '''
        Constructor.
        id - is the key unique field for a node with a given label.
        label - represents the node type. This could represents the entities in a system such as Person, Address, Dog etc.
                Equivalent to a table name in a relational DB.
        properties - key value pair of node propeties. This represents the entity attributes.
                     Property is equivalent to a column in a relational DB.
        connections - A set represents the relations to other nodes.
                      This is barely equivalent to forien keys used for joining in a relational DB.
        '''

        self.label = label
        self.properties = {"id": id}
        self.connections = set()

    def addConnection(self, node):
        '''
        Add an undirected connection to another node.
        '''

        if node == self:
            raise Exception("Cannot connect onself.")

        if not isinstance(node, Node):
            raise Exception("Not a node.")

        self.connections.add(node)
        node.connections.add(self)

    def getConnections(self):
        return self.connections

    def getId(self):
        return self.properties["id"]

    def getLabel(self):
        return self.label

    def addProperties(self, properties):
        if "id" in properties:
            raise Exception("Reserved property id cannot be added/updated.")

        self.properties.update(properties)

    def addOrUpdateProperty(self, propertyName, value):
        if "id" == propertyName:
            raise Exception("Reserved property id cannot be added/updated.")
        self.properties.update({propertyName: value})

    def getProperties(self):
        return self.properties

    def getProperty(self, propertyName):
        if propertyName in self.properties:
            return self.properties[propertyName]
        return None

    def __repr__(self):
        return f"{{'label': '{self.label}', 'properties': {self.properties} }}"


class GraphDB:
    def __init__(self):
        '''
        Constructor.
            nodes - All nodes in the Database.
            indexStore - Stores set of indexes for all node properties, to enable constant time search by any property.
            allIndexSets - A list containing referenes to all index sets in index stores. This is to optimize deleting all indexes for a node.
        '''

        self.nodes = set()
        self.indexeStore = {}
        self.allIndexSets = []

    def index(self, label, keyName, keyValue, node):
        '''
        Adds index for a node by it's label, property name and propery value.
        '''

        if label not in self.indexeStore:
            # Adds a top level index store entry for the label
            self.indexeStore.update({label: {None: {None: set()}}})

        if keyName not in self.indexeStore[label]:
            # Adds an entry for the property key under the label
            self.indexeStore[label].update({keyName: {}})

        if keyValue not in self.indexeStore[label][keyName]:
            # Adds a set for storing node references, under the property value (enables constat time search by any property value)
            newValueSet = set()
            self.indexeStore[label][keyName].update({keyValue: newValueSet})
            self.allIndexSets.append(newValueSet)

        self.indexeStore[label][keyName][keyValue].add(node)
        # All nodes under a label are grouped under key = None
        self.indexeStore[label][None][None].add(node)

    def query(self, queryQualifier=None):
        '''
        Search nodes by a parameter.
        Synatx: query(Label:property=value)
        Example: query(Person:gender=Male)
                 SQL equivalent: select * from Person p where p.gender = 'Male'

                 query(Person)
                 SQL equivalent: select * from Person

                 query()
                 SQL cannot do this easily - select * from all tables together.

        Returns a set of matching nodes, or an empty set if no match.
        '''

        if queryQualifier is None:
            return self.nodes

        label, key, value = GraphDB.parseQueryQualifier(queryQualifier)
        return self.indexeStore.get(label, {}).get(key, {}).get(value, set())

    def queryById(self, queryQualifier):
        '''
        Search nodes by node id.
        Synatx: queryById(Label:idValue)
        Example: queryById(Person:123)
                 SQL equivalent: select * from Person p where p.primaryKey = '123'

        Returns the node, or throws an exception if no node found with the id.
        '''

        label, key, value = GraphDB.parseQueryQualifier(queryQualifier)

        if key != "id":
            raise Exception(
                f"Invalid query format for searchById. try: \"{label}:{value}\"")

        try:
            return list(self.indexeStore[label][key][value])[0]
        except:
            raise Exception(f"No nodes of type {label} found with id: {value}")

    def graphQuery(self, nodeQualifier, query=None, maxDepth=100):
        '''
        Searches the relationship hierachy starting from a node, matched by the nodeQualifier
        Parameters:
            nodeQualifier - Id search qualifier to find the node where the search should start.
                            Syntax is same as that of searchById.
                            Syntax: Label:idValue
                            Example: Person:123
            query - Query filter to filter the children. This parameter is optional.
                    Synatx: property:value
                    Example: gender=Female
            maxDepth - How far down the search should be performed. Default is 100 levels.

        Returns:
            A dictionary with results, where the Key is the level and value is a set of matching connections at that level.

        Examples:
            graphQuery('Person:123')
            graphQuery('Person:123', 'gender=123', 5) # searches female connections of the person 123, upto 5 levels deep.

        '''

        startNode = self.queryById(nodeQualifier)
        return self.bfs(startNode, query, maxDepth)

    def bfs(self, startNode, query, maxDepth):
        '''
        Breadth first search starting at 'startNode', upto 'maxDepth' levels, filtered by the 'query'.
        A dictionary with results, where the Key is the level and value is a set of matching connections at that level.
        '''

        visited = set()
        level = 0
        result = {str(level): []}  # Initialize result with empty level 0

        q = Queue()
        q.enqueue(startNode)
        q.enqueue(None)  # Mark end of the level

        while not q.isEmpty() and level <= maxDepth:
            node = q.dequeue()
            if node is None:
                if q.peek() is None:  # Concecutive Nones indicate the end
                    break

                q.enqueue(None)  # Mark end of the level
                level += 1
                result.update({str(level): []})
                continue
            visited.add(node)

            if query is None or level == 0 or GraphDB.doesNodeMatchQuery(node, query):
                result[str(level)].append(node)

            for childNode in node.getConnections():
                if childNode not in visited:
                    q.enqueue(childNode)
                    visited.add(childNode)
        return result

    def addNode(self, label, id):
        '''
        Add a new node to the graph.
        Throws if node alreay exists.
        '''
        node = Node(id, label)

        self.verifyEntity(node)
        self.throwIfNodeAlreadyExists(node)

        self.nodes.add(node)
        self.reIndex(node)

    def connect(self, nodeQualifier1, nodeQualifier2):
        '''
        Adds a bi-directional (or undirected) relationship between two nodes.
        nodeQualifier1 and 2 -  Id search qualifier to find the node.
                                Syntax is same as that of searchById.
                                Syntax: Label:idValue
                                Example: Person:123
        '''

        node1 = self.queryById(nodeQualifier1)
        node2 = self.queryById(nodeQualifier2)

        node1.addConnection(node2)

    def addOrUpdateNodeProperty(self, nodeQualifier, propertyName, propertyValue):
        '''
        Add a propery to a node.

        Parameters:
            nodeQualifier - Id search qualifier to find the node where the properties need to be added.
                            Syntax is same as that of searchById.
                            Syntax: Label:idValue
                            Example: Person:123
            propertyName - name of the property (only strings supported as of now)
            propertyValue - value of the property (only strings supported as of now)
        '''

        node = self.queryById(nodeQualifier)
        node.addOrUpdateProperty(propertyName, propertyValue)
        self.reIndex(node)

    def throwIfNodeAlreadyExists(self, node):
        exists = False

        if node in self.nodes:
            exists = True
        else:
            try:
                existingNode = self.queryById(
                    f"{node.getLabel():{node.getId()}}")
                if existingNode is not None:
                    exists = True
            except:
                pass

        if exists:
            raise Exception(f"Node {node.id} already exists")

    def verifyEntity(self, node):
        if not isinstance(node, Node):
            raise Exception("Not a Node")

    def reIndex(self, node):
        '''
        Remove and re-add the indexes for a node when the node is changed/added
        '''

        self.unIndex(node)
        self.addIndex(node)

    def unIndex(self, node):
        for indexSet in self.allIndexSets:
            if node in indexSet:
                indexSet.remove(node)

    def addIndex(self, node):
        for propertyName, value in node.getProperties().items():
            self.index(node.getLabel(), propertyName, value, node)

    @staticmethod
    def doesNodeMatchQuery(node, query):
        '''
        Check if the node matches the given query.
        Query has the syntax: propertyName=propertyValue
        '''

        key, value = GraphDB.parseQueryClause(query)

        if key in node.getProperties():
            nodeVaule = node.getProperties()[key]
            return nodeVaule == value

        return False

    @staticmethod
    def parseQueryQualifier(queryQualifier):
        '''
        Parse a query qualifier of the followiong formats and return Label, Key, and Value
        Label:Key=Value or Label:NodeId
        ex: Person:gender=Female or Animal:123
        '''

        queryQualifierParts = queryQualifier.split(":")
        if len(queryQualifierParts) == 2:
            label = queryQualifierParts[0]
            query = queryQualifierParts[1]
            key, value = GraphDB.parseQueryClause(query)

            return label, key, value

        if len(queryQualifierParts) == 1:
            label = queryQualifierParts[0]
            return label, None, None

        raise Exception("Invalid Query")

    @staticmethod
    def parseQueryClause(query):
        '''
        Parse a query clause and returns key and value.
        Query clause has the syntax: propertyName=propertyValue
        '''

        queryParts = query.split("=")
        if len(queryParts) == 1:
            key = "id"
            value = queryParts[0]
            return key, value

        if len(queryParts) == 2:
            key = queryParts[0]
            value = queryParts[1]
            return key, value

        raise Exception("Invalid Query")


class ListNode:
    '''
    Represents a node in a linked list.
    '''

    def __init__(self, data):
        self.data = data
        self.next = None

    def getData(self):
        return self.data

    def getNext(self):
        return self.next

    def setData(self, data):
        self.data = data

    def setNext(self, next):
        self.next = next


class Queue:
    '''
    A Queue implementation using linked lists.
    '''

    def __init__(self):
        self.front = None
        self.back = None
        self.queueSize = 0

    def enqueue(self, item):
        node = ListNode(item)

        if self.isEmpty():
            self.front = node
            self.back = node
        else:
            self.back.setNext(node)
            self.back = node

        self.queueSize += 1

    def dequeue(self):
        if self.isEmpty():
            raise Exception("Queue is empty")

        item = self.front.getData()
        self.front = self.front.getNext()
        self.queueSize -= 1
        return item

    def peek(self):
        if not self.isEmpty():
            return self.front.getData()

    def isEmpty(self):
        return self.front is None

    def size(self):
        return self.queueSize


def test():
    global g
    g.addNode('Person', 'eljo')
    g.addNode('Person', 'merin')
    g.addNode('Person', 'norah')
    g.addNode('Dog', 'eljo')
    g.addOrUpdateNodeProperty('Person:eljo', 'name', 'Eljo George')
    g.addOrUpdateNodeProperty('Person:eljo', 'gender', 'Male')

    g.addOrUpdateNodeProperty('Person:merin', 'gender', 'Female')
    g.addOrUpdateNodeProperty('Person:norah', 'gender', 'Female')

    print(g.queryById('Person:eljo'))
    print(g.queryById('Person:merin'))
    print(g.queryById('Dog:eljo'))
    print(g.graphQuery('Person:eljo'))
    g.connect('Person:eljo', 'Person:norah')
    g.connect('Person:merin', 'Person:norah')
    print(g.graphQuery('Person:eljo'))
    g.connect('Person:merin', 'Person:eljo')
    print(g.graphQuery('Person:eljo'))
    print(g.graphQuery('Person:eljo'))

g = GraphDB()