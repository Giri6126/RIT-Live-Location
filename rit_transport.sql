-- ==============================================
-- RIT Live Location - Database Schema
-- Run this file once to set up the database
-- ==============================================

CREATE DATABASE IF NOT EXISTS rit_transport;
USE rit_transport;

-- Routes table
CREATE TABLE IF NOT EXISTS routes (
    route_id INT AUTO_INCREMENT PRIMARY KEY,
    route_name VARCHAR(100) NOT NULL
);

-- Buses table (includes password for driver login)
CREATE TABLE IF NOT EXISTS buses (
    bus_id INT AUTO_INCREMENT PRIMARY KEY,
    bus_number VARCHAR(20) NOT NULL,
    route_id INT NOT NULL,
    password VARCHAR(255) NOT NULL DEFAULT '1234',
    FOREIGN KEY (route_id) REFERENCES routes(route_id) ON DELETE CASCADE
);

-- Route stops (stores GPS coordinates for each stop along a route)
CREATE TABLE IF NOT EXISTS route_stops (
    id INT AUTO_INCREMENT PRIMARY KEY,
    route_id INT NOT NULL,
    stop_order INT NOT NULL DEFAULT 0,
    latitude DECIMAL(10,8) NOT NULL,
    longitude DECIMAL(11,8) NOT NULL,
    FOREIGN KEY (route_id) REFERENCES routes(route_id) ON DELETE CASCADE
);

-- Live locations table
CREATE TABLE IF NOT EXISTS live_locations (
    bus_id INT PRIMARY KEY,
    latitude DECIMAL(10,8) NOT NULL,
    longitude DECIMAL(11,8) NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bus_id) REFERENCES buses(bus_id) ON DELETE CASCADE
);

-- Arrival logs table
CREATE TABLE IF NOT EXISTS arrival_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bus_id INT NOT NULL,
    arrival_time DATETIME NOT NULL,
    recorded_by VARCHAR(50) DEFAULT 'system',
    FOREIGN KEY (bus_id) REFERENCES buses(bus_id) ON DELETE CASCADE
);


-- ==============================================
-- MIGRATION: Add password column if it doesn't exist
-- (Run this if upgrading an existing schema)
-- ==============================================
-- ALTER TABLE buses ADD COLUMN IF NOT EXISTS password VARCHAR(255) NOT NULL DEFAULT '1234';


-- ==============================================
-- SEED DATA (sample buses & routes for testing)
-- ==============================================

INSERT IGNORE INTO routes (route_id, route_name) VALUES
    (1, 'Route 1'),
    (2, 'Route 2'),
    (3, 'Route 3');

INSERT IGNORE INTO buses (bus_id, bus_number, route_id, password) VALUES
    (1, 'RIT-01', 1, '1234'),
    (2, 'RIT-02', 2, '1234'),
    (3, 'RIT-03', 3, '1234');

-- Route 1 stops (approaching college from north-west)
INSERT IGNORE INTO route_stops (route_id, stop_order, latitude, longitude) VALUES
    (1, 0, 13.0600, 80.0400),
    (1, 1, 13.0550, 80.0430),
    (1, 2, 13.0500, 80.0460),
    (1, 3, 13.0450, 80.0480),
    (1, 4, 13.0385, 80.0454);   -- College

-- Route 2 stops (approaching from east)
INSERT IGNORE INTO route_stops (route_id, stop_order, latitude, longitude) VALUES
    (2, 0, 13.0350, 80.0700),
    (2, 1, 13.0360, 80.0650),
    (2, 2, 13.0370, 80.0600),
    (2, 3, 13.0380, 80.0530),
    (2, 4, 13.0385, 80.0454);   -- College

-- Route 3 stops (approaching from south)
INSERT IGNORE INTO route_stops (route_id, stop_order, latitude, longitude) VALUES
    (3, 0, 13.0200, 80.0454),
    (3, 1, 13.0250, 80.0454),
    (3, 2, 13.0300, 80.0454),
    (3, 3, 13.0350, 80.0454),
    (3, 4, 13.0385, 80.0454);   -- College
