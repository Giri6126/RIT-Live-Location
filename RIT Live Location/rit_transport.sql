-- Routes table
CREATE TABLE routes (
    route_id INT AUTO_INCREMENT PRIMARY KEY,
    route_name VARCHAR(50) NOT NULL
);

-- Buses table
CREATE TABLE buses (
    bus_id INT AUTO_INCREMENT PRIMARY KEY,
    bus_number VARCHAR(20) NOT NULL,
    route_id INT NOT NULL,
    FOREIGN KEY (route_id) REFERENCES routes(route_id)
);

-- Live locations table
CREATE TABLE live_locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bus_id INT NOT NULL,
    latitude DECIMAL(10,8) NOT NULL,
    longitude DECIMAL(11,8) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bus_id) REFERENCES buses(bus_id) ON DELETE CASCADE
);

-- Arrival logs table
CREATE TABLE arrival_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bus_id INT NOT NULL,
    arrival_time DATETIME NOT NULL,
    recorded_by VARCHAR(50) DEFAULT 'system',
    FOREIGN KEY (bus_id) REFERENCES buses(bus_id)
);
