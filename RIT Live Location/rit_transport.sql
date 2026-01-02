-- Buses table
CREATE TABLE IF NOT EXISTS buses (
    bus_id INT AUTO_INCREMENT PRIMARY KEY,
    bus_number VARCHAR(20) NOT NULL,
    route_id INT NOT NULL
);

-- Routes table
CREATE TABLE IF NOT EXISTS routes (
    route_id INT AUTO_INCREMENT PRIMARY KEY,
    route_name VARCHAR(50) NOT NULL
);

-- Live locations table
CREATE TABLE IF NOT EXISTS live_locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bus_id INT NOT NULL,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bus_id) REFERENCES buses(bus_id)
);

-- Arrival logs table
CREATE TABLE IF NOT EXISTS arrival_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bus_id INT NOT NULL,
    arrival_time DATETIME NOT NULL,
    recorded_by VARCHAR(50) DEFAULT 'system',
    FOREIGN KEY (bus_id) REFERENCES buses(bus_id)
);
CREATE TABLE IF NOT EXISTS live_locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bus_id VARCHAR(10),
    latitude DOUBLE,
    longitude DOUBLE,
    timestamp DATETIME
);

CREATE TABLE IF NOT EXISTS arrival_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bus_id VARCHAR(10),
    arrival_time DATETIME,
    recorded_by VARCHAR(50)
);
