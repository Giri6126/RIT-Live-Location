RIT Live Bus Tracking System

Real-time bus tracking system for Rajalakshmi Institute of Technology (RIT) — built using Flask (Python), MySQL, HTML/CSS, and JavaScript.
This project enables drivers to share live GPS, and students to track their bus in real-time.

Table of Contents
Overview
Features
Project Architecture
Folder Structure
Tech Stack
API Endpoints
Database Structure
Setup Instructions
How the System Works (Full Flow)
Contribution Guide

Future Enhancements

 1. Overview
This project solves a real problem for college students — no more waiting for the bus blindly.
The system has three interfaces:

 Driver
Shares live GPS every few seconds
The backend stores the location in MySQL
The system logs arrival when bus reaches within 50m radius of campus

 Student
Can select their route number
Sees bus movement LIVE on Google Maps
Updated every few seconds

Admin
Manage buses, drivers, routes
View arrival logs
Monitor live status

2. Features
Live Bus Tracking
Drivers send continuous GPS coordinates which are displayed to students in real-time.
GPS Sharing
Driver page uses the browser’s GPS API to capture location.

 REST API
Clean Flask endpoints for live location updates and fetching latest bus location.

🧭 Haversine Distance Calculation
Used to check when the bus reaches college (arrival logs).

🗺 Google Maps Integration
Students get a clean, smooth, interactive map showing bus movement.

🗄 MySQL Database
Stores bus info, live locations, and arrival logs.

🏗 3. Project Architecture (Backend + Frontend)
Backend (Flask):
API receives location (/api/update_location)
Validates data
Stores in MySQL
Applies Haversine formula
Detects arrival within 50m
Sends JSON response back to frontend

Frontend (HTML + JS):

Driver Page:
Gets current GPS
Sends it to backend using fetch() API
Start/Stop sharing buttons

Student Page:
Loads Google Map
Fetches latest location
Updates marker position live

Database (MySQL):
buses → route, bus number
live_locations → every GPS update
arrival_logs → arrival timestamps

4. Folder Structure

RIT-Live-Location/
│
├── app.py                     # Flask backend
├── config.py                  # DB connection config
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation
│
├── templates/                 # Frontend HTML
│   ├── base.html
│   ├── index.html
│   ├── driver.html
│   ├── student.html
│   └── admin.html
│
├── static/
│   ├── css/
│   │    └── styles.css
│   ├── js/
│   │    ├── driver.js
│   │    ├── student.js
│   │    └── admin.js
│   └── images/
│        ├── bus.png
│        └── driver.png
│
└── rit_transport.sql          # MySQL database file

🧰 5. Tech Stack

Backend
Python
Flask
MySQL
Frontend
HTML
CSS
JavaScript
Google Maps API

How the System Works (Full Flow Summary)

Driver Side
Driver chooses bus
Clicks Start Sharing
Browser sends GPS to backend every 5 seconds
Backend inserts into MySQL
If bus reaches within 50m → arrival logged
Student Side
Student chooses bus route
Google Map loads
JS fetches new location every few seconds
Bus marker animates smoothly on map
Admin Side
View all buses
View live locations
Arrivals
Manage master data

