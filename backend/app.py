import math
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from config import get_db_connection
from datetime import datetime

# Serve the Vite-built React frontend from the dist/ folder
DIST_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")

app = Flask(__name__, static_folder=DIST_FOLDER, static_url_path="")
app.secret_key = "rit_live_location_secret_key"

# Enable CORS for all routes so the React frontend can communicate
CORS(app)

# College coordinates and arrival radius
COLLEGE_LATITUDE = 13.03849
COLLEGE_LONGITUDE = 80.04536
ARRIVAL_RADIUS_KM = 0.05  # 50 meters

# ---------------------------
# HELPER: Haversine formula
# ---------------------------
def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    R = 6371  # km
    return R * c


# ---------------------------
# SERVE REACT (Lovable) FRONTEND
# ---------------------------
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    """Catch-all: serve the Vite-built React SPA.
    API routes (/api/*) are matched before this catch-all so they are unaffected.
    All other paths return index.html so React Router handles client-side routing.
    """
    # If the path matches a real file in dist/ (JS, CSS, images, etc.), serve it directly
    full_path = os.path.join(DIST_FOLDER, path)
    if path and os.path.exists(full_path):
        return send_from_directory(DIST_FOLDER, path)
    # Otherwise fall back to index.html for React Router
    return send_from_directory(DIST_FOLDER, "index.html")


# ==============================================================
# DRIVER APIS
# ==============================================================

# POST /api/update_location
@app.route("/api/update_location", methods=["POST"])
def update_location():
    data = request.get_json()
    bus_id = data.get("bus_id")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    landmark = data.get("landmark")  # landmark is optional

    if bus_id is None or latitude is None or longitude is None:
        return jsonify({"status": "error", "message": "Missing fields"}), 400

    try:
        bus_id = int(bus_id)
        latitude = float(latitude)
        longitude = float(longitude)
    except Exception:
        return jsonify({"status": "error", "message": "Invalid bus_id or coordinates"}), 400

    conn = cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "error", "message": "DB connection failed"}), 500
        cursor = conn.cursor()

        # UPSERT: Insert new location or update existing for the bus_id
        # We also set is_active = TRUE because this endpoint is called when sharing is active
        cursor.execute(
            """
            INSERT INTO live_locations (bus_id, latitude, longitude, landmark, is_active, timestamp) 
            VALUES (%s, %s, %s, %s, TRUE, NOW())
            ON DUPLICATE KEY UPDATE 
                latitude = VALUES(latitude), 
                longitude = VALUES(longitude),
                landmark = VALUES(landmark),
                is_active = TRUE,
                timestamp = NOW()
            """,
            (bus_id, latitude, longitude, landmark),
        )

        # ALSO UPDATE THE 'buses' TABLE STATUS (NEW REQUIREMENT)
        cursor.execute(
            """
            UPDATE buses 
            SET latitude = %s, longitude = %s, status = 'moving'
            WHERE bus_id = %s
            """,
            (latitude, longitude, bus_id)
        )
        conn.commit()
        print(f"Bus {bus_id} is sharing location: Lat {latitude}, Lon {longitude}, Landmark: {landmark}")

        # Auto-detect arrival at college
        dist = haversine(latitude, longitude, COLLEGE_LATITUDE, COLLEGE_LONGITUDE)
        if dist <= ARRIVAL_RADIUS_KM:
            cursor.execute(
                "INSERT INTO arrival_logs (bus_id, arrival_time) VALUES (%s, %s)",
                (bus_id, datetime.now()),
            )
            conn.commit()
            print(f"🏫 Bus {bus_id} arrived at college!")

        return jsonify({"status": "success", "message": "Location updated, sharing active"})

    except Exception as e:
        if conn:
            conn.rollback()
        print("❌ DB ERROR [update_location]:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# POST /api/stop_sharing
@app.route("/api/stop_sharing", methods=["POST"])
def stop_sharing():
    data = request.get_json()
    bus_id = data.get("bus_id")

    if bus_id is None:
        return jsonify({"status": "error", "message": "Missing bus_id"}), 400

    print(f"🛑 Bus {bus_id} requested to STOP sharing")

    conn = cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "error", "message": "DB connection failed"}), 500
        cursor = conn.cursor()

        # DELETE the row completely — this is the fail-safe.
        # Using UPDATE is_active=FALSE is NOT enough because a stale interval
        # can fire update_location (ON DUPLICATE KEY UPDATE) and re-activate it.
        cursor.execute(
            "DELETE FROM live_locations WHERE bus_id = %s",
            (bus_id,)
        )
        conn.commit()
        print(f"\n🛑🛑🛑 Bus {bus_id} has STOPPED sharing location and removed from all maps 🛑🛑🛑\n")

        # Verify deletion
        cursor.execute("SELECT * FROM live_locations WHERE bus_id = %s", (bus_id,))
        print("After stop (should be None):", cursor.fetchone())

        return jsonify({"status": "success", "message": "Sharing stopped"})

    except Exception as e:
        if conn:
            conn.rollback()
        print("❌ DB ERROR [stop_sharing]:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# GET /api/get_bus_status?bus_id=101
@app.route("/api/get_bus_status", methods=["GET"])
def get_bus_status():
    bus_id = request.args.get("bus_id")
    if not bus_id:
        return jsonify({"status": "error", "message": "Missing bus_id"}), 400

    conn = cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "error", "message": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT status FROM buses WHERE bus_id = %s", (bus_id,))
        result = cursor.fetchone()
        if result:
            return jsonify({"status": "success", "bus_status": result["status"]})
        return jsonify({"status": "error", "message": "Bus not found"}), 404
    except Exception as e:
        print("❌ DB ERROR [get_bus_status]:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# POST /api/stop_location
@app.route("/api/stop_location", methods=["POST"])
def stop_location():
    data = request.get_json()
    bus_id = data.get("bus_id")
    if bus_id is None:
        return jsonify({"status": "error", "message": "Missing bus_id"}), 400

    conn = cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "error", "message": "DB connection failed"}), 500
        cursor = conn.cursor()
        
        # Update buses status to parked
        cursor.execute("UPDATE buses SET status = 'parked' WHERE bus_id = %s", (bus_id,))
        
        # Fail-safe: also deactivate in live_locations
        cursor.execute("DELETE FROM live_locations WHERE bus_id = %s", (bus_id,))
        
        conn.commit()
        print(f"✅ Bus {bus_id} marked as PARKED")
        return jsonify({"status": "success", "message": "Bus stopped and marked as parked"})
    except Exception as e:
        if conn:
            conn.rollback()
        print("❌ DB ERROR [stop_location]:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# POST /api/driver/login
@app.route("/api/driver/login", methods=["POST"])
def driver_login():
    data = request.get_json()
    print("🔑 [driver_login] Received:", data)

    bus_id = data.get("bus_id")
    password = data.get("password")

    if not bus_id or not password:
        return jsonify({"status": "error", "message": "Missing bus_id or password"}), 400

    conn = cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "error", "message": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT b.bus_id, b.bus_number, r.route_name AS route_number
            FROM buses b
            LEFT JOIN routes r ON b.route_id = r.route_id
            WHERE b.bus_id = %s AND b.password = %s
            """,
            (bus_id, password),
        )
        bus = cursor.fetchone()

        if bus:
            print(f"✅ Driver login success for bus {bus_id}")
            return jsonify({
                "status": "success",
                "bus_id": bus["bus_id"],
                "bus_number": bus["bus_number"],
                "route_number": bus["route_number"],
            })
        else:
            print(f"⚠️ Driver login failed for bus {bus_id}")
            return jsonify({"status": "error", "message": "Invalid bus ID or password"}), 401

    except Exception as e:
        print("❌ DB ERROR [driver_login]:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==============================================================
# STUDENT APIS
# ==============================================================

# GET /api/get_all_locations  — latest location of every active bus
@app.route("/api/get_all_locations", methods=["GET"])
def get_all_locations():
    conn = cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            print("❌ [get_all_locations] DB connection failed")
            return jsonify([]), 200  # Return empty array, not error object
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT ll.bus_id, ll.latitude, ll.longitude, ll.landmark,
                   ll.timestamp, b.bus_number,
                   r.route_name AS route_number
            FROM live_locations ll
            JOIN buses b ON ll.bus_id = b.bus_id
            LEFT JOIN routes r ON b.route_id = r.route_id
            WHERE ll.is_active = TRUE
            ORDER BY ll.bus_id
            """
        )
        locations = cursor.fetchall()

        # ── CRITICAL FIX: Convert Decimal → float, datetime → str ──
        # MySQL returns DECIMAL columns as Python Decimal objects which
        # are NOT JSON-serializable.  We must convert them to float.
        result = []
        for loc in locations:
            result.append({
                "bus_id":       int(loc["bus_id"]),
                "latitude":     float(loc["latitude"]),
                "longitude":    float(loc["longitude"]),
                "landmark":     loc.get("landmark", ""),
                "bus_number":   loc.get("bus_number", ""),
                "route_number": loc.get("route_number", ""),
                "timestamp":    str(loc["timestamp"]) if loc.get("timestamp") else None,
            })

        # ── Required Debug Log ──
        print("Active buses:", result)

        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("❌ DB ERROR [get_all_locations]:", e)
        return jsonify([]), 200  # Return empty array so frontend doesn't crash
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# NEW API → GET /api/get_all_buses
@app.route("/api/get_all_buses", methods=["GET"])
def get_all_buses():
    conn = cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify([]), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT bus_id FROM buses")
        buses = cursor.fetchall()
        # Format: [{ "bus_id": 101 }, { "bus_id": 102 }]
        result = [{"bus_id": b["bus_id"]} for b in buses]
        return jsonify(result)
    except Exception as e:
        print("❌ DB ERROR [get_all_buses]:", e)
        return jsonify([]), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# GET /api/get_location/<bus_id>
@app.route("/api/get_location/<bus_id>", methods=["GET"])
def get_location(bus_id):
    conn = cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "error", "message": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT latitude, longitude, timestamp FROM live_locations WHERE bus_id=%s AND is_active=TRUE LIMIT 1",
            (bus_id,),
        )
        result = cursor.fetchone()
        if result:
            result["timestamp"] = str(result["timestamp"])
            return jsonify({"status": "success", "location": result})
        return jsonify({"status": "error", "message": "No active location found"}), 404
    except Exception as e:
        print("❌ DB ERROR [get_location]:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# GET /api/get_routes  — returns {route_key: [[lat, lng], ...]} dict
@app.route("/api/get_routes", methods=["GET"])
def get_routes():
    conn = cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "error", "message": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT r.route_id, r.route_name,
                   rs.latitude, rs.longitude, rs.stop_order
            FROM routes r
            JOIN route_stops rs ON r.route_id = rs.route_id
            ORDER BY r.route_id, rs.stop_order
            """
        )
        rows = cursor.fetchall()

        routes: dict = {}
        for row in rows:
            key = f"route_{row['route_id']}"
            if key not in routes:
                routes[key] = []
            routes[key].append([float(row["latitude"]), float(row["longitude"])])

        print(f"🗺️  [get_routes] Returning {len(routes)} routes")
        return jsonify(routes)

    except Exception as e:
        print("❌ DB ERROR [get_routes]:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# GET /api/arrival_logs  — recent arrival log (latest entry)
@app.route("/api/arrival_logs", methods=["GET"])
def arrival_logs():
    conn = cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "error", "message": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT al.id, al.bus_id, al.arrival_time,
                   b.bus_number, r.route_name AS route_number
            FROM arrival_logs al
            JOIN buses b ON al.bus_id = b.bus_id
            LEFT JOIN routes r ON b.route_id = r.route_id
            ORDER BY al.arrival_time DESC
            LIMIT 20
            """
        )
        logs = cursor.fetchall()
        for log in logs:
            if log.get("arrival_time"):
                log["arrival_time"] = str(log["arrival_time"])
            log["bus_id"] = str(log["bus_id"])

        print(f"📋 [arrival_logs] Returning {len(logs)} logs")
        return jsonify(logs)

    except Exception as e:
        print("❌ DB ERROR [arrival_logs]:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# GET /api/eta/<bus_id>  — calculate ETA to college based on last known location
@app.route("/api/eta/<int:bus_id>", methods=["GET"])
def get_eta(bus_id):
    conn = cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "error", "message": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT latitude, longitude FROM live_locations WHERE bus_id=%s ORDER BY timestamp DESC LIMIT 1",
            (bus_id,),
        )
        loc = cursor.fetchone()
        if not loc:
            return jsonify({"status": "error", "message": "No location data"}), 404

        dist_km = haversine(
            float(loc["latitude"]), float(loc["longitude"]),
            COLLEGE_LATITUDE, COLLEGE_LONGITUDE,
        )
        # Assume average speed of 30 km/h
        eta_minutes = (dist_km / 30) * 60

        if eta_minutes < 1:
            eta_str = "< 1 min"
        elif eta_minutes < 60:
            eta_str = f"{int(eta_minutes)} min"
        else:
            eta_str = f"{int(eta_minutes // 60)}h {int(eta_minutes % 60)}m"

        return jsonify({"status": "success", "bus_id": bus_id, "eta": eta_str, "distance_km": round(dist_km, 2)})

    except Exception as e:
        print("❌ DB ERROR [get_eta]:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==============================================================
# ADMIN APIS
# ==============================================================

# GET /api/admin/stats
@app.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    conn = cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "error", "message": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) AS total FROM buses")
        total_buses = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(DISTINCT bus_id) AS active FROM live_locations WHERE timestamp >= NOW() - INTERVAL 5 MINUTE")
        active_buses = cursor.fetchone()["active"]

        cursor.execute("SELECT COUNT(*) AS total FROM routes")
        total_routes = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM arrival_logs WHERE DATE(arrival_time) = CURDATE()")
        today_arrivals = cursor.fetchone()["total"]

        return jsonify({
            "status": "success",
            "total_buses": total_buses,
            "active_buses": active_buses,
            "offline_buses": total_buses - active_buses,
            "total_routes": total_routes,
            "today_arrivals": today_arrivals,
        })
    except Exception as e:
        print("❌ DB ERROR [admin_stats]:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# GET /api/admin/buses
@app.route("/api/admin/buses", methods=["GET"])
def get_buses():
    conn = cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "error", "message": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT b.bus_id AS id, b.bus_number,
                   r.route_name AS route_number,
                   MAX(ll.timestamp) AS last_updated
            FROM buses b
            LEFT JOIN routes r ON b.route_id = r.route_id
            LEFT JOIN live_locations ll ON b.bus_id = ll.bus_id
            GROUP BY b.bus_id, b.bus_number, r.route_name
            ORDER BY b.bus_id
            """
        )
        buses = cursor.fetchall()
        for bus in buses:
            if bus.get("last_updated"):
                ts = bus["last_updated"]
                bus["last_updated"] = str(ts)
                # Mark bus active if updated within last 5 minutes
                diff = (datetime.now() - ts).total_seconds()
                bus["status"] = "active" if diff < 300 else "idle"
            else:
                bus["status"] = "offline"

        print(f"🚌 [get_buses] Returning {len(buses)} buses")
        return jsonify(buses)

    except Exception as e:
        print("❌ DB ERROR [get_buses]:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# POST /api/admin/add_bus
@app.route("/api/admin/add_bus", methods=["POST"])
def add_bus():
    data = request.get_json()
    print("➕ [add_bus] Received:", data)

    bus_number = data.get("bus_number")
    route_number = data.get("route_number")
    password = data.get("password")

    if not bus_number or not route_number or not password:
        return jsonify({"status": "error", "message": "Missing fields"}), 400

    conn = cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "error", "message": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        # Find or create route
        cursor.execute("SELECT route_id FROM routes WHERE route_name = %s", (route_number,))
        route = cursor.fetchone()
        if route:
            route_id = route["route_id"]
        else:
            cursor.execute("INSERT INTO routes (route_name) VALUES (%s)", (route_number,))
            route_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO buses (bus_number, route_id, password) VALUES (%s, %s, %s)",
            (bus_number, route_id, password),
        )
        conn.commit()
        print(f"✅ Bus added: {bus_number} on route {route_number}")
        return jsonify({"status": "success", "message": "Bus added"})

    except Exception as e:
        if conn:
            conn.rollback()
        print("❌ DB ERROR [add_bus]:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# DELETE /api/admin/delete_bus
@app.route("/api/admin/delete_bus", methods=["DELETE"])
def delete_bus():
    data = request.get_json()
    bus_id = data.get("bus_id") if data else None

    if not bus_id:
        return jsonify({"status": "error", "message": "Missing bus_id"}), 400

    conn = cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "error", "message": "DB connection failed"}), 500
        cursor = conn.cursor()
        cursor.execute("DELETE FROM buses WHERE bus_id = %s", (bus_id,))
        conn.commit()
        print(f"🗑️  Bus {bus_id} deleted")
        return jsonify({"status": "success", "message": "Bus deleted"})

    except Exception as e:
        if conn:
            conn.rollback()
        print("❌ DB ERROR [delete_bus]:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# POST /api/admin/add_route
@app.route("/api/admin/add_route", methods=["POST"])
def add_route():
    data = request.get_json()
    print("➕ [add_route] Received:", data)

    route_name = data.get("route_name")
    stops = data.get("stops", [])  # list of "lat,lng" strings or objects

    if not route_name:
        return jsonify({"status": "error", "message": "Missing route_name"}), 400

    conn = cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "error", "message": "DB connection failed"}), 500
        cursor = conn.cursor()

        cursor.execute("INSERT INTO routes (route_name) VALUES (%s)", (route_name,))
        route_id = cursor.lastrowid

        for idx, stop in enumerate(stops):
            if isinstance(stop, str) and "," in stop:
                lat, lng = stop.split(",", 1)
            elif isinstance(stop, (list, tuple)) and len(stop) >= 2:
                lat, lng = stop[0], stop[1]
            else:
                continue
            cursor.execute(
                "INSERT INTO route_stops (route_id, stop_order, latitude, longitude) VALUES (%s, %s, %s, %s)",
                (route_id, idx, float(lat), float(lng)),
            )

        conn.commit()
        print(f"✅ Route added: {route_name} with {len(stops)} stops")
        return jsonify({"status": "success", "message": "Route added", "route_id": route_id})

    except Exception as e:
        if conn:
            conn.rollback()
        print("❌ DB ERROR [add_route]:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# DELETE /api/admin/delete_route
@app.route("/api/admin/delete_route", methods=["DELETE"])
def delete_route():
    data = request.get_json()
    route_id_raw = data.get("route_id") if data else None

    if not route_id_raw:
        return jsonify({"status": "error", "message": "Missing route_id"}), 400

    # route_id may arrive as "route_3" or just "3"
    route_id_str = str(route_id_raw).replace("route_", "")
    try:
        route_id = int(route_id_str)
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid route_id"}), 400

    conn = cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "error", "message": "DB connection failed"}), 500
        cursor = conn.cursor()
        cursor.execute("DELETE FROM route_stops WHERE route_id = %s", (route_id,))
        cursor.execute("DELETE FROM routes WHERE route_id = %s", (route_id,))
        conn.commit()
        print(f"🗑️  Route {route_id} deleted")
        return jsonify({"status": "success", "message": "Route deleted"})

    except Exception as e:
        if conn:
            conn.rollback()
        print("❌ DB ERROR [delete_route]:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# POST /api/admin/update_bus_password
@app.route("/api/admin/update_bus_password", methods=["POST"])
def update_bus_password():
    data = request.get_json()
    bus_id = data.get("bus_id")
    password = data.get("password")

    if not bus_id or not password:
        return jsonify({"status": "error", "message": "Missing fields"}), 400

    conn = cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "error", "message": "DB connection failed"}), 500
        cursor = conn.cursor()
        cursor.execute("UPDATE buses SET password = %s WHERE bus_id = %s", (password, bus_id))
        conn.commit()
        return jsonify({"status": "success", "message": "Password updated"})

    except Exception as e:
        if conn:
            conn.rollback()
        print("❌ DB ERROR [update_bus_password]:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# GET /api/get_buses_by_route/<route_id>  (legacy)
@app.route("/api/get_buses_by_route/<int:route_id>", methods=["GET"])
def get_buses_by_route(route_id):
    conn = cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "error", "message": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT bus_id, bus_number FROM buses WHERE route_id=%s", (route_id,))
        buses = cursor.fetchall()
        return jsonify({"status": "success", "buses": buses})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# GET /api/get_arrival/<bus_id>  (legacy)
@app.route("/api/get_arrival/<bus_id>", methods=["GET"])
def get_arrival(bus_id):
    conn = cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "error", "message": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM arrival_logs WHERE bus_id=%s ORDER BY arrival_time DESC LIMIT 1",
            (bus_id,),
        )
        result = cursor.fetchone()
        if result:
            result["arrival_time"] = str(result["arrival_time"])
            return jsonify({"status": "success", "arrival_time": result["arrival_time"]})
        return jsonify({"status": "pending", "message": "Bus has not arrived yet"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ---------------------------
# RUN FLASK APP
# ---------------------------
if __name__ == "__main__":
    print("Starting RIT Live Location backend on http://127.0.0.1:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
