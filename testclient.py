import requests

BASE = "http://127.0.0.1:5000"

tests = [
    ("getData", {"key": "999", "start": "2022-11-23 05:28:10", "end": "2022-11-23 05:28:15"}),
    ("getData", {"key": "123", "start": "2022-11-23 05:28:10"}),
    ("getData", {"key": "123", "start": "bad", "end": "2022-11-23 05:28:15"}),
    ("getData", {"key": "123", "start": "2022-11-23 05:28:10", "end": "2022-11-23 05:28:15"}),
    ("countInPolygon", {"polygon": "-74 42,-75 39,-74 41,-74 42"}),
    ("countInPolygon", {"key": "123", "polygon": "-74 42,-75"}),
    ("countInPolygon", {"key": "123", "polygon": "-74 42,-75 39,-74 41,-74 42"}),
    ("getAvgSpeedByFlight", {"key": "abc"}),
    ("getAvgSpeedByFlight", {"key": "123", "start": "2022-11-23 05:00:00", "end": "2022-11-23 08:00:00"}),
    ("getAvgSpeedByFlight", {"key": "123"}),
]

for endpoint, params in tests:
    r = requests.get(f"{BASE}/{endpoint}", params=params)
    resp = r.json()
    print(f"{endpoint} {params}")
    print(f"  code: {resp['code']}  msg: {resp['msg']}  req: {resp['req']}  sqltime: {resp['sqltime']:.4f}")
    if "count" in resp:
        print(f"  count: {resp['count']}")
    if resp.get("results"):
        print(f"  first result: {resp['results'][0]}")
    print()
