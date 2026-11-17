# ADSB Flask API

Flask API over the `class_datapoints` ADSB table on the class MySQL server.

## Files

- `main.py`: the API
- `testclient.py`: test client that calls every endpoint
- `setup.sql`: auth and logging tables (`kanotugm_auth`, `kanotugm_logs`), run automatically when `main.py` starts
- `schemas.json`: JSON schema for each endpoint response
- `config.yml`: database connection settings

## Run

```
pip install flask pymysql pyyaml requests
python main.py
python testclient.py
```

Base URL: `http://127.0.0.1:5000`

## Endpoints

All requests need `key=123`.

| Endpoint | Parameters | Notes |
|---|---|---|
| `/getData` | `key`, `start`, `end` | Datapoints between start and end. Both dates required. Max 500 rows. |
| `/countInPolygon` | `key`, `polygon` | Count of datapoints inside the polygon, e.g. `-74 42,-75 39,-74 41,-74 42` |
| `/getAvgSpeedByFlight` | `key`, `start`, `end` | Average ground speed per flight. Dates optional. Max 500 rows. |

Dates use the format `YYYY-MM-DD HH:MM:SS`.

## Response

Every response has these top level keys:

- `code`: 1 success, 0 failure
- `msg`: result message, or the reason for failure
- `req`: endpoint name
- `sqltime`: SQL query time in seconds

Successful responses add `count`, and `results` where a list is returned. Full schemas are in `schemas.json`.

## Auth and logging

- A request is accepted only when `key` is 123 and that token is active in `kanotugm_auth`.
- Every request, passed or failed, is written to `kanotugm_logs` with token, endpoint, parameters, code, message, SQL time, IP and timestamp.
