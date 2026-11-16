import pandas as pd
from neo4j import GraphDatabase

# converting csv to dict for neo4j
df = pd.read_csv("taxi_trips_clean.csv")
rows = df.to_dict("records")

# connecting to neo4j
uri = "bolt://localhost:7687"
auth = ("neo4j", "12345678")
driver = GraphDatabase.driver(uri = uri, auth = auth)

with driver.session() as session:
    session.run("""
        UNWIND $rows AS row
        
        MERGE (d:Driver {driver_id: row.driver_id})
        MERGE (c:Company {name: row.company})
        MERGE (a:Area {area_id: row.dropoff_area})

        MERGE (d)-[:WORKS_FOR]->(c)

        CREATE (d)-[:TRIP {
            trip_id: row.trip_id,
            fare: row.fare,
            trip_seconds: row.trip_seconds
        }]->(a)
    """, rows=rows).consume()

driver.close()
print("Taxi data successfully loaded into Neo4j database.")
        
