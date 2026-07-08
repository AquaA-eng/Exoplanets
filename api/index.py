import sqlite3
import os
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="NASA Exoplanet Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "nasa_exoplanets.db")


def query_db(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(sql, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


@app.get("/")
def root():
    return {
        "message": "NASA Exoplanet Assistant API",
        "endpoints": [
            "/planets/closest-habitable",
            "/planets/smallest",
            "/planets/largest",
            "/planets/search",
            "/stats/summary",
            "/stats/by-method",
            "/stars/most-planets",
        ],
    }


@app.get("/planets/closest-habitable")
def closest_habitable(
    max_distance: float = Query(50, description="Max distance in light years"),
    min_radius: float = Query(0.5, description="Min radius in Earth radii"),
    max_radius: float = Query(1.6, description="Max radius in Earth radii"),
):
    sql = """
        SELECT e.planet_name, s.star_name, s.distance_ly, e.radius_earth,
               e.mass_earth, e.temp_kelvin, e.orbital_period_days, e.eccentricity,
               s.star_temp_kelvin, s.star_type,
               m.method_name, e.discovery_year
        FROM exoplanets e
        JOIN stars s ON e.star_id = s.star_id
        JOIN discovery_methods m ON e.method_id = m.method_id
        WHERE s.distance_ly < ? AND e.radius_earth BETWEEN ? AND ?
        ORDER BY s.distance_ly ASC
    """
    return query_db(sql, (max_distance, min_radius, max_radius))


@app.get("/planets/smallest")
def smallest_planet():
    sql = "SELECT planet_name, radius_earth FROM exoplanets ORDER BY radius_earth ASC LIMIT 1"
    return query_db(sql)


@app.get("/planets/largest")
def largest_planet():
    sql = "SELECT planet_name, radius_earth FROM exoplanets ORDER BY radius_earth DESC LIMIT 1"
    return query_db(sql)


@app.get("/planets/search")
def search_planets(
    max_distance: float = Query(None),
    min_radius: float = Query(None),
    max_radius: float = Query(None),
    method: str = Query(None, description="Discovery method, e.g. Transit"),
    limit: int = Query(50),
):
    sql = """
        SELECT e.planet_name, s.star_name, s.distance_ly, e.radius_earth,
               e.mass_earth, e.temp_kelvin, e.orbital_period_days, e.eccentricity,
               s.star_temp_kelvin, s.star_type,
               m.method_name, e.discovery_year
        FROM exoplanets e
        JOIN stars s ON e.star_id = s.star_id
        JOIN discovery_methods m ON e.method_id = m.method_id
        WHERE 1=1
    """
    params = []
    if max_distance is not None:
        sql += " AND s.distance_ly <= ?"
        params.append(max_distance)
    if min_radius is not None:
        sql += " AND e.radius_earth >= ?"
        params.append(min_radius)
    if max_radius is not None:
        sql += " AND e.radius_earth <= ?"
        params.append(max_radius)
    if method is not None:
        sql += " AND m.method_name = ?"
        params.append(method)
    sql += " ORDER BY s.distance_ly ASC LIMIT ?"
    params.append(limit)
    return query_db(sql, tuple(params))


@app.get("/stats/summary")
def summary_stats():
    sql = """
        SELECT COUNT(*) as total_planets,
               MIN(discovery_year) as earliest_year,
               MAX(discovery_year) as latest_year,
               SUM(CASE WHEN radius_earth <= 6 THEN 1 ELSE 0 END) as rocky_count,
               SUM(CASE WHEN radius_earth > 6 THEN 1 ELSE 0 END) as gas_giant_count
        FROM exoplanets
    """
    return query_db(sql)[0]


@app.get("/stats/by-method")
def stats_by_method():
    sql = """
        SELECT m.method_name, COUNT(*) as planet_count,
               ROUND(AVG(e.radius_earth), 2) as avg_radius
        FROM exoplanets e
        JOIN discovery_methods m ON e.method_id = m.method_id
        GROUP BY m.method_name
        ORDER BY planet_count DESC
    """
    return query_db(sql)


@app.get("/stars/most-planets")
def most_planets(limit: int = Query(5)):
    sql = """
        SELECT s.star_name, COUNT(*) as planet_count
        FROM exoplanets e
        JOIN stars s ON e.star_id = s.star_id
        GROUP BY s.star_name
        ORDER BY planet_count DESC
        LIMIT ?
    """
    return query_db(sql, (limit,))


@app.get("/stats/avg-planets-per-star")
def avg_planets_per_star():
    sql = """
        SELECT ROUND(AVG(planet_count), 2) as avg_planets_per_star
        FROM (SELECT star_id, COUNT(*) as planet_count FROM exoplanets GROUP BY star_id)
    """
    return query_db(sql)[0]


@app.get("/stats/single-vs-multi")
def single_vs_multi():
    sql = """
        SELECT
            SUM(CASE WHEN planet_count = 1 THEN 1 ELSE 0 END) as single_planet_systems,
            SUM(CASE WHEN planet_count > 1 THEN 1 ELSE 0 END) as multi_planet_systems
        FROM (SELECT star_id, COUNT(*) as planet_count FROM exoplanets GROUP BY star_id)
    """
    return query_db(sql)[0]


@app.get("/stats/orbit-records")
def orbit_records():
    shortest = query_db("""
        SELECT planet_name, orbital_period_days FROM exoplanets
        WHERE orbital_period_days > 0 ORDER BY orbital_period_days ASC LIMIT 1
    """)[0]
    longest = query_db("""
        SELECT planet_name, orbital_period_days FROM exoplanets
        ORDER BY orbital_period_days DESC LIMIT 1
    """)[0]
    return {"shortest": shortest, "longest": longest}


@app.get("/stats/orbits-under")
def orbits_under(days: float = Query(10)):
    sql = "SELECT COUNT(*) as count FROM exoplanets WHERE orbital_period_days > 0 AND orbital_period_days < ?"
    return query_db(sql, (days,))[0]


@app.get("/stats/by-year")
def by_year():
    sql = """
        SELECT discovery_year, COUNT(*) as planet_count
        FROM exoplanets GROUP BY discovery_year ORDER BY discovery_year ASC
    """
    return query_db(sql)


@app.get("/stats/recent-methods")
def recent_methods(years: int = Query(5)):
    sql = """
        SELECT m.method_name, COUNT(*) as planet_count
        FROM exoplanets e JOIN discovery_methods m ON e.method_id = m.method_id
        WHERE e.discovery_year >= (SELECT MAX(discovery_year) FROM exoplanets) - ?
        GROUP BY m.method_name ORDER BY planet_count DESC
    """
    return query_db(sql, (years,))


@app.get("/stats/avg-distance")
def avg_distance():
    return query_db("SELECT ROUND(AVG(distance_ly), 1) as avg_distance_ly FROM stars")[0]


@app.get("/planets/beyond")
def planets_beyond(min_distance: float = Query(1000)):
    sql = """
        SELECT COUNT(*) as count
        FROM exoplanets e JOIN stars s ON e.star_id = s.star_id
        WHERE s.distance_ly > ?
    """
    return query_db(sql, (min_distance,))[0]
