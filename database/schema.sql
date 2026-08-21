-- ============================================================================
-- Environmental Intelligence Pipeline Database Schema (PostgreSQL)
-- Data Sources: OpenAQ (Air Quality) + USGS (Earthquakes)
-- ============================================================================

-- Drop tables if they exist (for clean schema initialization)
DROP TABLE IF EXISTS air_quality_readings CASCADE;
DROP TABLE IF EXISTS earthquake_events CASCADE;
DROP TABLE IF EXISTS locations CASCADE;
DROP TABLE IF EXISTS pipeline_runs CASCADE;

-- 1. Locations Metadata Table
CREATE TABLE locations (
    location_id INT PRIMARY KEY,
    location_name VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    country VARCHAR(100),
    latitude NUMERIC(10, 6),
    longitude NUMERIC(10, 6),
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2. Air Quality Readings Table
CREATE TABLE air_quality_readings (
    measurement_id BIGINT PRIMARY KEY,
    location_id INT NOT NULL REFERENCES locations(location_id) ON DELETE CASCADE,
    location_name VARCHAR(255),
    city VARCHAR(100),
    country VARCHAR(100),
    latitude NUMERIC(10, 6),
    longitude NUMERIC(10, 6),
    parameter VARCHAR(50) NOT NULL,
    value NUMERIC(12, 4) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    normalized_value NUMERIC(12, 4),
    normalized_unit VARCHAR(50),
    aqi_us_epa INT,
    reading_timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT idx_unique_aq_reading UNIQUE (location_id, parameter, reading_timestamp)
);

-- 3. Earthquake Events Table
CREATE TABLE earthquake_events (
    event_id VARCHAR(50) PRIMARY KEY,
    event_time TIMESTAMPTZ NOT NULL,
    magnitude NUMERIC(4, 2) NOT NULL,
    magnitude_type VARCHAR(20),
    place VARCHAR(255),
    region VARCHAR(150),
    longitude NUMERIC(10, 6) NOT NULL,
    latitude NUMERIC(10, 6) NOT NULL,
    depth_km NUMERIC(8, 2) NOT NULL,
    magnitude_category VARCHAR(30) NOT NULL,
    status VARCHAR(50),
    event_type VARCHAR(50),
    tsunami INT DEFAULT 0,
    event_url TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 4. Pipeline Audit & Metadata Table
CREATE TABLE pipeline_runs (
    run_id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    records_extracted INT DEFAULT 0,
    records_loaded INT DEFAULT 0,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    error_message TEXT
);

-- Indexes for optimized querying and aggregation performance
CREATE INDEX idx_aq_reading_timestamp ON air_quality_readings (reading_timestamp);
CREATE INDEX idx_aq_location_id ON air_quality_readings (location_id);
CREATE INDEX idx_aq_parameter ON air_quality_readings (parameter);
CREATE INDEX idx_eq_event_time ON earthquake_events (event_time);
CREATE INDEX idx_eq_magnitude ON earthquake_events (magnitude);
CREATE INDEX idx_eq_category ON earthquake_events (magnitude_category);
CREATE INDEX idx_eq_coordinates ON earthquake_events (latitude, longitude);
