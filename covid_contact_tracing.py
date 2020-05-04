from graphdb.graphdb import GraphDB
import csv


class Action:
    '''
    Represents an action which user can choose to run from the menu.
    '''

    def __init__(self, description, action, graphDB):
        self.description = description
        self.action = action
        self.graphDB = graphDB

    def show(self):
        print(self.description)

    def run(self):
        print("\n-------------------------------")
        return self.action(self.graphDB)


def listInfectedPeople(graphDB):
    '''
    Print list of infected people.
    '''

    infectedPeople = graphDB.query("Person:infected=yes")
    for person in infectedPeople:
        print(person)


def determinZone(personId, graphDB):
    '''
    Determine the current risk zoning for a person.
    Infected - The person is infected
    Red - Person has a direct contact who is infected
    Orange - Person has a second level contact who is infected
    Green - Neither person nor his first or second level contacts are infected.
    '''

    graph = graphDB.graphQuery(f"Person:{personId}", "infected=yes", 2)

    if '0' in graph and graph['0']:
        person = graph['0'][0]
        if person.getProperty('infected') == 'yes':
            return "Infected"

    if '1' in graph and graph['1']:
        return "Red"

    if '2' in graph and graph['2']:
        return "Orange"

    return "Green"


def printContactNetwork(graphDB):
    '''
    Print the contact network graph by level, for a person.
    '''

    personId = input("Enter person Id: ")
    depth = int(input("How many levels? "))
    graph = graphDB.graphQuery(f"Person:{personId}", maxDepth=depth)
    printGraphWithZone(graph, graphDB)


def markInfectedPerson(graphDB):
    '''
    Mark a person as infected.
    This will put their first level contacts at least to Red zone.
    This will put their second level contacts at least to Orange zone.
    '''

    personId = input("Enter person Id: ")
    graphDB.addOrUpdateNodeProperty(f"Person:{personId}", "infected", "yes")

    print(
        f"Since {personId} is infected, their neighbours' Zone might have affected negatively.")
    graph = graphDB.graphQuery(f"Person:{personId}", maxDepth=2)
    printGraphWithZone(graph, graphDB)


def markRecoveredPerson(graphDB):
    '''
    Mark an infected person as recovered.
    This can possibly put their contacts at Green zone.
    '''

    personId = input("Enter person Id: ")
    graphDB.addOrUpdateNodeProperty(f"Person:{personId}", "infected", "no")

    print(
        f"Since {personId} is recovered, their neighbours' Zone might have changed positively.")
    graph = graphDB.graphQuery(f"Person:{personId}", maxDepth=2)
    printGraphWithZone(graph, graphDB)


def printGraphWithZone(graph, graphDB):
    '''
    Helper method for printing people in a graph with their respective zone.
    '''

    for level, contacts in graph.items():
        print(f"Level {level} =>")
        for contact in contacts:
            contactZone = determinZone(contact.getId(), graphDB)
            print(f"\tZone: {contactZone}, Details: {contact}")


def populateData(graphDB):
    '''
    Load people and their connections into the Graph DB, from csv files.
    '''

    peopleDataFileName = input(
        "Enter people data file name: ") or r"data\people.csv"
    contactDataFileName = input(
        "Enter contact data file name: ") or r"data\contact.csv"

    personNodeLabel = "Person"

    # Add people from csv
    with open(peopleDataFileName, newline='') as peopleDataFile:
        peopleDataReader = csv.reader(peopleDataFile)
        propertyNames = next(peopleDataReader)

        if len(propertyNames) == 0:
            raise Exception("Empty header")
        if propertyNames and propertyNames[0] != "id":
            raise Exception("First property must be id")

        for row in peopleDataReader:
            id = row[0]
            graphDB.addNode(personNodeLabel, id)
            nodeQualifier = personNodeLabel + ":" + id

            for i in range(1, len(propertyNames)):
                graphDB.addOrUpdateNodeProperty(
                    nodeQualifier, propertyNames[i], row[i])

    # Add people contacts/connections from csv
    with open(contactDataFileName, newline='') as contactDataFile:
        contactDataReader = csv.reader(contactDataFile)
        for row in contactDataReader:
            person1Id = row[0]
            person2Id = row[1]

            person1Qualifier = personNodeLabel + ":" + person1Id
            person2Qualifier = personNodeLabel + ":" + person2Id

            graphDB.connect(person1Qualifier, person2Qualifier)


def main():
    graphDB = GraphDB()
    populateData(graphDB)

    actions = {
        '1': Action("List infected people.", listInfectedPeople, graphDB),
        '2': Action("Print contact network for a specific person.", printContactNetwork, graphDB),
        '3': Action("Mark a person as infected.", markInfectedPerson, graphDB),
        '4': Action("Mark a person as recovered.", markRecoveredPerson, graphDB)
    }

    choice = ''

    while choice != 'q':
        print("\n-----------------------------------------")
        print("Options")
        for option, action in actions.items():
            print(f"{option} - {action.description}")

        choice = input("Enter your choice: ")

        if choice in actions:
            try:
                actions[choice].run()
            except Exception as e:
                print(e)

            input("\nHit enter to continue...")


main()
