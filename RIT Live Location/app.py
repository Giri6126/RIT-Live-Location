import math
from flask import Flask, request, jsonify, render_template
from config import get_db_connection
from datetime import datetime
from math import radians, cos, sin, asin, sqrt

app = Flask(__name__)
app.secret_key = "rit_live_location_secret_key"

# College coordinates and arrival radius
COLLEGE_LATITUDE = 13.03849
COLLEGE_LONGITUDE = 80.04536
ARRIVAL_RADIUS_KM = 0.05  # 50 meters

# Haversine formula
def haversine(lat1, lon1, lat2, lon2):
    # convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    c = 2*math.asin(math.sqrt(a))
    R = 6371  # Radius of earth in km
    return R * c
# ---------------------------
# ROUTES
# ---------------------------
@app.route("/")
def home():
    return render_template("login.html")

@app.route("/driver")
def driver_page():
    return render_template("driver.html")

@app.route("/student")
def student_page():
    return render_template("student.html")

@app.route("/admin")
def admin_page():
    return render_template("admin.html")

# ---------------------------
# API: Update location
# ---------------------------
@app.route("/api/update_location", methods=["POST"])
def update_location():
    data = request.get_json()
    print("Received JSON:", data)  # <--- debug

    bus_id = data.get("bus_id")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if bus_id is None or latitude is None or longitude is None:
        return jsonify({"status":"error","message":"Missing fields"}), 400

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except Exception as e:
        print("Error converting lat/lon:", e)
        return jsonify({"status":"error","message":"Invalid latitude/longitude"}), 400

    print("Bus:", bus_id, "Lat:", latitude, "Lon:", longitude)
    ...


# ---------------------------
# API: Get latest bus location
# ---------------------------
@app.route("/api/get_location/<bus_id>", methods=["GET"])
def get_location(bus_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT latitude, longitude, timestamp FROM live_locations WHERE bus_id=%s ORDER BY timestamp DESC LIMIT 1",
        (bus_id,)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        return jsonify({"status": "success", "location": result})
    return jsonify({"status": "error", "message": "No location found"})

# ---------------------------
# API: Get buses by route
# ---------------------------
@app.route("/api/get_buses_by_route/<int:route_id>", methods=["GET"])
def get_buses_by_route(route_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT bus_id, bus_number FROM buses WHERE route_id=%s", (route_id,))
    buses = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "buses": buses})

# ---------------------------
# API: Get arrival status
# ---------------------------
@app.route("/api/get_arrival/<bus_id>", methods=["GET"])
def get_arrival(bus_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM arrival_logs WHERE bus_id=%s ORDER BY arrival_time DESC LIMIT 1",
        (bus_id,)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        return jsonify({"status": "success", "arrival_time": result["arrival_time"]})
    return jsonify({"status": "pending", "message": "Bus has not arrived yet"})

import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Giri2006@",
        database="rit_transport"
    )

# ---------------------------
# RUN FLASK APP
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
