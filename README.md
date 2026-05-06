# RIT Live Location — Setup & Run Guide

## Prerequisites

| Tool | Install from |
|---|---|
| Python 3.10+ | https://python.org |
| MySQL 8.0+ | https://dev.mysql.com/downloads/ |
| Node.js 18+ | https://nodejs.org |

---

## 1. Database Setup

Open MySQL and run the schema file **once**:

```sql
-- In MySQL Workbench or mysql CLI:
source D:/git/RIT Live Location/rit_transport.sql
```

This creates the `rit_transport` database with all tables and inserts 3 sample buses (RIT-01, RIT-02, RIT-03) all with password `1234`.

> **If you already have the old schema**, run this migration to add the new columns:
> ```sql
> USE rit_transport;
> ALTER TABLE buses ADD COLUMN IF NOT EXISTS password VARCHAR(255) NOT NULL DEFAULT '1234';
> CREATE TABLE IF NOT EXISTS route_stops (
>     id INT AUTO_INCREMENT PRIMARY KEY,
>     route_id INT NOT NULL,
>     stop_order INT NOT NULL DEFAULT 0,
>     latitude DECIMAL(10,8) NOT NULL,
>     longitude DECIMAL(11,8) NOT NULL,
>     FOREIGN KEY (route_id) REFERENCES routes(route_id) ON DELETE CASCADE
> );
> ```

---

## 2. Configure Database Credentials

Edit `config.py` if your MySQL credentials differ from the defaults:

```python
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="YOUR_PASSWORD",   # ← change this
    database="rit_transport"
)
```

---

## 3. Install Python Dependencies

```bash
pip install flask flask-cors mysql-connector-python
```

Or using the requirements file:

```bash
pip install -r requirement.txt
```

---

## 4. Start the Flask Backend

```bash
cd "D:/git/RIT Live Location"
python app.py
```

You should see:
```
 Starting RIT Live Location backend on http://127.0.0.1:5000
 * Running on http://0.0.0.0:5000
```

---

## 5. Install Frontend Dependencies

```bash
cd "D:/git/RIT Live Location"
npm install
```

---

## 6. Start the React Frontend

```bash
npm run dev
```

Frontend runs at: **http://localhost:8080**

---

## 7. Using the Application

### As a Student
1. Open http://localhost:8080
2. Click **Student Access**
3. The map shows all active buses updated every 5 seconds

### As a Driver
1. Open http://localhost:8080
2. Click **Driver Login**
3. Select your bus (e.g. RIT-01) and enter the password (`1234` by default)
4. Click **Start Sharing Location** — your GPS is sent to the backend every 5 seconds

### As Admin
1. Open http://localhost:8080
2. Click **Admin Login**
3. View the live map, manage buses, routes, and arrival logs

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/update_location` | Driver sends GPS coords |
| POST | `/api/driver/login` | Driver authenticates |
| GET | `/api/get_all_locations` | Latest position of each bus |
| GET | `/api/get_routes` | Route polyline coordinates |
| GET | `/api/arrival_logs` | Recent college arrivals |
| GET | `/api/eta/<bus_id>` | ETA to college |
| GET | `/api/admin/buses` | All buses |
| POST | `/api/admin/add_bus` | Add a bus |
| DELETE | `/api/admin/delete_bus` | Remove a bus |
| POST | `/api/admin/add_route` | Add a route |
| DELETE | `/api/admin/delete_route` | Remove a route |
| POST | `/api/admin/update_bus_password` | Change bus password |

---

## Environment Variables

The frontend reads `VITE_API_URL` from `.env`:

```
VITE_API_URL=http://127.0.0.1:5000
```

Copy `.env.example` to `.env` if it doesn't exist yet.

---

## Architecture

```
Browser (React + Leaflet)          Flask (Python)           MySQL
      port 8080           ←CORS→      port 5000          rit_transport DB
         │                               │
         │  GET /api/get_all_locations   │  SELECT latest locations
         │  POST /api/update_location    │  INSERT live_locations
         │  POST /api/driver/login       │  SELECT buses WHERE password
         └───────────────────────────────┘
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `CORS error` in browser console | Make sure `python app.py` is running |
| `DB connection failed` in Flask logs | Check MySQL is running and credentials in `config.py` |
| Map shows demo data only | Backend is unreachable — check port 5000 |
| Driver login fails | Ensure `buses.password` column exists (run migration above) |
| `npm: not recognized` | Install Node.js from https://nodejs.org |
