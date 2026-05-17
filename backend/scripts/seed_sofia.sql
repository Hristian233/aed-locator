-- AED Locator — Sofia, Bulgaria sample data
-- Run after migrations: alembic upgrade head
--
-- Usage (psql):
--   psql -U aed -d aed_locator -f scripts/seed_sofia.sql
--
-- Or via Docker:
--   docker compose exec db psql -U aed -d aed_locator -f /path/to/seed_sofia.sql

CREATE EXTENSION IF NOT EXISTS postgis;

-- Clear existing rows (safe for empty or re-seed)
TRUNCATE TABLE aeds RESTART IDENTITY CASCADE;
TRUNCATE TABLE users RESTART IDENTITY CASCADE;

-- ---------------------------------------------------------------------------
-- Users
-- Passwords:
--   admin@aedlocator.local  -> adminchange1
--   reporter@example.com    -> reporter123
-- ---------------------------------------------------------------------------
INSERT INTO users (email, hashed_password, full_name, role, is_active) VALUES
(
  'admin@aedlocator.local',
  '$2b$12$RTpb7sG/NAqzDJoVc6hPD.idSkwO.xda17MfJI2n9sq/kr0HpYe/e',
  'Sofia Admin',
  'admin',
  TRUE
),
(
  'reporter@example.com',
  '$2b$12$dI6l3z54I8m4oDlpzJZQfOcLM8ZmyiaVjZYf28An/hqgTAUNyj7/S',
  'Demo Reporter',
  'user',
  TRUE
);

-- ---------------------------------------------------------------------------
-- Verified AEDs (shown on the public map)
-- location: PostGIS POINT (longitude, latitude), SRID 4326
-- ---------------------------------------------------------------------------
INSERT INTO aeds (
  location,
  latitude,
  longitude,
  address,
  description,
  verification_status,
  submitter_id,
  ai_confidence,
  spam_score
) VALUES
(
  ST_SetSRID(ST_MakePoint(23.3189, 42.6853), 4326)::geography,
  42.6853, 23.3189,
  'NDK — National Palace of Culture',
  'Main entrance foyer, left of the information desk',
  'verified', 2, 0.94, 0.03
),
(
  ST_SetSRID(ST_MakePoint(23.3219, 42.6977), 4326)::geography,
  42.6977, 23.3219,
  'Serdika Metro Station',
  'Concourse level near exit to Vitosha Boulevard',
  'verified', 2, 0.91, 0.04
),
(
  ST_SetSRID(ST_MakePoint(23.3342, 42.6934), 4326)::geography,
  42.6934, 23.3342,
  'Sofia University Rectorate',
  'Ground floor lobby, security desk area',
  'verified', 2, 0.89, 0.05
),
(
  ST_SetSRID(ST_MakePoint(23.3213, 42.7114), 4326)::geography,
  42.7114, 23.3213,
  'Sofia Central Railway Station',
  'Main hall, near the western ticket counters',
  'verified', 2, 0.92, 0.02
),
(
  ST_SetSRID(ST_MakePoint(23.4142, 42.6950), 4326)::geography,
  42.6950, 23.4142,
  'Sofia Airport — Terminal 2',
  'Departures hall, after security checkpoint area (landside)',
  'verified', 2, 0.88, 0.06
),
(
  ST_SetSRID(ST_MakePoint(23.3448, 42.6885), 4326)::geography,
  42.6885, 23.3448,
  'Borisova Gradina Park',
  'Park entrance near Ariana Lake, kiosk building',
  'verified', 2, 0.90, 0.04
),
(
  ST_SetSRID(ST_MakePoint(23.3095, 42.6980), 4326)::geography,
  42.6980, 23.3095,
  'Mall of Sofia',
  'Ground floor near the central atrium escalators',
  'verified', 2, 0.93, 0.02
),
(
  ST_SetSRID(ST_MakePoint(23.3144, 42.6869), 4326)::geography,
  42.6869, 23.3144,
  'Medical University Sofia',
  'Faculty building A, main corridor ground floor',
  'verified', 2, 0.87, 0.05
),
(
  ST_SetSRID(ST_MakePoint(23.3190, 42.6910), 4326)::geography,
  42.6910, 23.3190,
  'Vitosha Boulevard — Patriarch Evtimiy',
  'Pharmacy entrance, staff can direct to AED cabinet',
  'verified', 2, 0.91, 0.03
),
(
  ST_SetSRID(ST_MakePoint(23.3765, 42.6570), 4326)::geography,
  42.6570, 23.3765,
  'Paradise Center',
  'Cinema level, next to first-aid room signage',
  'verified', 2, 0.86, 0.07
),
(
  ST_SetSRID(ST_MakePoint(23.3420, 42.6690), 4326)::geography,
  42.6690, 23.3420,
  'Arena Armeec Sofia',
  'Event hall concourse, staff entrance B',
  'verified', 2, 0.85, 0.08
),
(
  ST_SetSRID(ST_MakePoint(23.3525, 42.6780), 4326)::geography,
  42.6780, 23.3525,
  'National Stadium Vasil Levski',
  'West stand concourse, level 1',
  'verified', 2, 0.90, 0.04
);

-- ---------------------------------------------------------------------------
-- Pending submissions (admin queue — not on public map until verified)
-- ---------------------------------------------------------------------------
INSERT INTO aeds (
  location,
  latitude,
  longitude,
  address,
  description,
  verification_status,
  submitter_id,
  ai_confidence,
  spam_score
) VALUES
(
  ST_SetSRID(ST_MakePoint(23.3580, 42.6720), 4326)::geography,
  42.6720, 23.3580,
  'Lozenets District Municipality',
  'Reception area, reported by citizen — awaiting photo review',
  'pending', 2, 0.62, 0.18
),
(
  ST_SetSRID(ST_MakePoint(23.3670, 42.6480), 4326)::geography,
  42.6480, 23.3670,
  'Studentski grad — Block 8',
  'Ground floor entrance, near security booth',
  'pending', 2, 0.58, 0.22
),
(
  ST_SetSRID(ST_MakePoint(23.2930, 42.7100), 4326)::geography,
  42.7100, 23.2930,
  'Lyulin Metro Station',
  'Platform level — needs verifier site visit',
  'pending', 2, 0.55, 0.25
);

-- Reset sequences to max(id)
SELECT setval(pg_get_serial_sequence('users', 'id'), COALESCE((SELECT MAX(id) FROM users), 1));
SELECT setval(pg_get_serial_sequence('aeds', 'id'), COALESCE((SELECT MAX(id) FROM aeds), 1));

SELECT 'Seeded Sofia data:' AS status,
  (SELECT COUNT(*) FROM users) AS users,
  (SELECT COUNT(*) FROM aeds WHERE verification_status = 'verified') AS verified_aeds,
  (SELECT COUNT(*) FROM aeds WHERE verification_status = 'pending') AS pending_aeds;
