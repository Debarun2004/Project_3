# PrithibiRoute Backend

Backend API for Dynamic Route-Optimization & CO₂ Footprint Estimator for Fleet Logistics.

## Development

Activate the existing Windows virtual environment in PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies and run tests:

```powershell
python -m pip install -r requirements.txt
python -m pytest
```

Start the development server:

```powershell
python -m uvicorn app.main:app --reload
```

The API documentation is available at `http://127.0.0.1:8000/docs`.

## API endpoints

- `GET /health`
- `POST /routes/compare`
- `POST /routes/optimize`
- `POST /routes/network`
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/drivers`
- `POST /api/v1/drivers`
- `GET /api/v1/trucks`
- `POST /api/v1/trucks`
- `GET /api/v1/trips`
- `POST /api/v1/trips`

Fleet list/dashboard APIs read records from MySQL by default. Route comparison
and optimization are still synthetic connectivity responses. The initial
fleet and trip entries are fictional sample records; their contact numbers,
licences, vehicle registrations, and route estimates are not real and must not
be used to contact anyone or make operational decisions.

## MySQL

The backend uses the local MySQL service by default. In MySQL Workbench, sign
in with an administrative account and create a database and a dedicated
application user (replace the sample password with a strong password of your
own):

```sql
CREATE DATABASE IF NOT EXISTS prithibiroute CHARACTER SET utf8mb4;
CREATE USER IF NOT EXISTS 'prithibiroute_app'@'127.0.0.1'
  IDENTIFIED BY 'choose_a_strong_local_password';
GRANT SELECT, INSERT, CREATE ON prithibiroute.* TO 'prithibiroute_app'@'127.0.0.1';
```

Copy `.env.example` to `.env`, then set `MYSQL_PASSWORD` to the same password
you chose for the application user. Do not use the MySQL root account for the
backend, commit `.env`, or share your password. Start the API with:

```powershell
Copy-Item .env.example .env
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

On startup, the app verifies the MySQL connection and creates the `drivers`,
`trucks`, and `trips` tables if they do not exist. With
`MYSQL_SEED_DEMO_DATA=true`, it inserts the supplied fake records only when all
three tables are empty; it never replaces existing fleet records. Set
`DATA_SOURCE=demo` to use JSON data explicitly for tests or offline work.
Connection/configuration errors stop startup rather than silently switching
data sources.

The checked-in sample fleet uses fictional names and synthetic 10-digit
contact-number values. Licence and vehicle registration values are fictional.
Do not call the listed numbers or use these records as real fleet credentials.
After making the sample data more presentable, update an existing local
database once with:

```powershell
python -m scripts.update_seeded_fleet
```

The script updates only rows with the original `driver-demo-*`,
`truck-demo-*`, and `trip-demo-*` IDs, renames those IDs, and updates their
references. It leaves records created with other IDs unchanged. It requires
`UPDATE` permission on the application database; if necessary, grant it from
an administrative Workbench connection:

```sql
GRANT UPDATE ON prithibiroute.* TO 'prithibiroute_app'@'127.0.0.1';
```

### Importing and using the OSM road network

The supplied `.osm.pbf` is read-only. Import a bounded Kolkata/Howrah/New Town
region into the project's derived SQLite road-graph file (not MySQL fleet data):

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m scripts.import_osm_pbf --pbf "C:\Users\HP\Downloads\ml_proj\ml_proj\eastern-zone-261022.osm.pbf"
```

The default bounding box is `88.15,22.35,88.65,22.75`; supply
`--bbox MIN_LON MIN_LAT MAX_LON MAX_LAT` to change it. Re-running the importer
rebuilds the derived `data/road_network.sqlite` file. Do not point `--output`
at the source PBF or MySQL database.

`POST /routes/network` accepts source/destination labels, their latitude and
longitude coordinates, and `preference` (`fastest` or `shortest`). The frontend
must geocode place selections and send their coordinates. The API snaps each
point to a road within 2 km, follows one-way directions, and returns a route
geometry and distance. Travel time uses OSM maxspeed tags or documented
road-class defaults; it is not live traffic. Fuel and CO₂ are returned as
`null` until the ML models are integrated. The existing `/routes/compare` and
`/routes/optimize` endpoints remain synthetic connectivity responses.

### Adding fleet records

Use the `POST` endpoints in `/docs` to add drivers, trucks, or trips. The API
generates record IDs and saves each new record to MySQL. Driver phone values
must contain exactly 10 digits. The driver, truck, and trip `GET` endpoints
will include newly created records. Writes return `503` in explicit demo mode.

Example driver request:

```json
{
  "name": "Example Driver",
  "phone": "9876543210",
  "licence_number": "FAKE-LIC-100",
  "experience_years": 3,
  "rating": 4.5,
  "status": "off_duty"
}
```

The existing fake demo records are not automatically replaced or edited by
these create endpoints.

Truck payload capacity is stored and returned using the field name `Payload`
(kilograms). If your MySQL database already has the older `capacity_kg` column,
stop the backend and connect to MySQL Workbench with your administrator
account. Run this one-time migration before restarting the backend:

```sql
USE prithibiroute;
ALTER TABLE trucks RENAME COLUMN capacity_kg TO Payload;
```

This renames the column and preserves its existing values. Alternatively, the
project migration command can be used by a database login with `ALTER`
permission: `python -m scripts.migrate_truck_payload`. New truck requests
should send `"Payload": 5000`.

## Routing baseline

`app.services.road_network.build_road_graph` builds a directed NetworkX graph
from already-loaded edge records. Each edge must include `source_node`,
`target_node`, `length_km`, `travel_time_minutes`,
`fuel_consumption_liters`, and `co2_emissions_kg`.

`app.services.routing.find_routes` returns fastest, greenest, and balanced
candidate routes for node IDs in that graph. The graph service is not yet
connected to the HTTP route endpoints. The graph builder does not download
data, geocode places, or predict missing fuel/emissions values.
