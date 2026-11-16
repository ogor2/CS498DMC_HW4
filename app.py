from flask import Flask, request
from neo4j import GraphDatabase

app = Flask(__name__)

uri = "bolt://localhost:7687"
auth = ("neo4j", "YOUR_PASSWORD")
driver = GraphDatabase.driver(uri=uri, auth=auth)

# returns counts of each attribute and trip relationship
@app.route("/graph-summary")
def graph_summary():
    summary = driver.execute_query("""
        MATCH (d:Driver)
        WITH count(d) as driver_count
        MATCH (c:Company)
        WITH driver_count, count(c) as company_count
        MATCH (a:Area)
        WITH driver_count, company_count, count(a) as area_count
        MATCH (d)-[t:Trip]->(a)
        RETURN driver_count, company_count, area_count, count(t) as trip_count
    """).records[0]

    return {
        "driver_count": summary["driver_count"],
        "company_count":summary["company_count"],
        "area_count":summary["area_count"],
        "trip_count":summary["trip_count"]
    }

# return top companies by trip amount
@app.route("/top-companies")
def top_companies():
    n = request.args.get("n", default=5, type=int)
    companies = driver.execute_query("""
        MATCH (c:Company)<-[:WORKS_FOR]-(d:Driver)-[t:TRIP]->(:Area)
        RETURN c.name AS name, count(t) AS trip_count
        ORDER BY trip_count DESC, name ASC
        LIMIT $n
    """, n=n).records

    return {
      "companies":[
        {"name": company["name"], "trip_count": company["trip_count"]}
              for company in companies
      ]
    }

# returns fairs above min fair in specific area
@app.route("/high-fare-trips")
def high_fare_trips():
    area_id = request.args.get("area_id", type=int)
    min_fare = request.args.get("min_fare", type=float)

    fairs = driver.execute_query("""
        MATCH (d:Driver)-[t:TRIP]->(a:Area)
        WHERE a.area_id = $area_id AND t.fare >$min_fare
        RETURN t.trip_id AS trip_id, t.fare AS fare, d.driver_id AS driver_id
        ORDER BY fare DESC, trip_id ASC
    """, area_id=area_id, min_fare=min_fare).records

    return {
        "trips": [
            {
                "trip_id": fair["trip_id"], "fare": fair["fare"], "driver_id": fair["driver_id"]
            }
            for fair in fairs
        ]
    }

# returns other drivers who have dropped off in the same area
@app.route("/co-area-drivers")
def co_area_drivers():
    driver_id = request.args.get("driver_id")

    other_drivers = driver.execute_query("""
        MATCH (d1:Driver)-[:TRIP]->(a:Area)<-[:TRIP]-(d2:Driver)
        WHERE d1.driver_id = $driver_id AND d1 <> d2
        RETURN d2.driver_id AS driver_id, count(DISTINCT a) AS shared_areas
        ORDER BY shared_areas DESC, driver_id ASC
    """, driver_id=driver_id).records

    return {
        "co_area_drivers": [
            {
                "driver_id": o["driver_id"], "shared_areas": o["shared_areas"]
            }
            for o in other_drivers
        ]
    }

# returns the average fair amount by company 
@app.route("/avg-fare-by-company")
def avg_fare_by_company():
    companies = driver.execute_query("""
        MATCH (c:Company)<-[:WORKS_FOR]-(d:Driver)-[t:TRIP]->(:Area)
        RETURN c.name AS name, round(avg(t.fare),2) AS avg_fare
        ORDER BY avg_fare DESC, name ASC
    """).records
    return {
        "companies": [
            {
                "name": c["name"],"avg_fare": c["avg_fare"]
            }
            for c in companies
        ]
    }
  
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)













