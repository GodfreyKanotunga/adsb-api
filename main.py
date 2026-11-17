import json
import time
import datetime
import decimal
import pymysql
import yaml
from flask import Flask, request, Response

app = Flask(__name__)

with open("config.yml", "r") as file:
    dbconfig = yaml.safe_load(file)["mysql"]

VALIDKEY = "123"
DATEFORMAT = "%Y-%m-%d %H:%M:%S"
LIMIT = 500


def connect():
    return pymysql.connect(**dbconfig, cursorclass=pymysql.cursors.DictCursor)


def setup():
    with open("setup.sql", "r") as file:
        statements = [s.strip() for s in file.read().split(";") if s.strip()]
    conn = connect()
    try:
        with conn.cursor() as cur:
            for statement in statements:
                cur.execute(statement)
        conn.commit()
    finally:
        conn.close()


def clean(value):
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.strftime(DATEFORMAT)
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, (bytes, bytearray)):
        return None
    return value


def cleanrow(row):
    return {k: clean(v) for k, v in row.items() if not isinstance(v, (bytes, bytearray))}


def validdate(text):
    if text is None:
        return False
    try:
        datetime.datetime.strptime(text, DATEFORMAT)
        return True
    except ValueError:
        return False


def auth(key):
    if key is None or key != VALIDKEY:
        return False
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT `id` FROM `kanotugm_auth` WHERE `token` = %s AND `active` = 1;", (key,))
            return len(cur.fetchall()) == 1
    finally:
        conn.close()


def log(key, endpoint, res):
    conn = connect()
    try:
        with conn.cursor() as cur:
            sql = ("INSERT INTO `kanotugm_logs` (`token`, `endpoint`, `params`, `code`, `msg`, `sqltime`, `ip`, `dt`) "
                   "VALUES (%s, %s, %s, %s, %s, %s, %s, %s);")
            cur.execute(sql, (
                key,
                endpoint,
                json.dumps(request.args.to_dict()),
                res.get("code"),
                res.get("msg"),
                res.get("sqltime"),
                request.remote_addr,
                datetime.datetime.now().strftime(DATEFORMAT),
            ))
        conn.commit()
    except Exception as e:
        print(str(e))
    finally:
        conn.close()


def reply(endpoint, res):
    log(request.args.get("key"), endpoint, res)
    return Response(json.dumps(res, indent=4), mimetype="application/json")


def fail(endpoint, msg):
    res = {"code": 0, "msg": msg, "req": endpoint, "sqltime": 0}
    return reply(endpoint, res)


def checkauth(endpoint):
    try:
        if not auth(request.args.get("key")):
            return fail(endpoint, "auth error: invalid or missing key")
    except Exception as e:
        return fail(endpoint, "auth error: " + str(e))
    return None


def runquery(sql, params):
    conn = connect()
    try:
        with conn.cursor() as cur:
            start = time.time()
            cur.execute(sql, params)
            rows = cur.fetchall()
            sqltime = time.time() - start
        return rows, sqltime
    finally:
        conn.close()


@app.route("/", methods=["GET"])
def root():
    res = {"code": 0, "msg": "No endpoint specified", "req": "/", "sqltime": 0}
    return Response(json.dumps(res, indent=4), mimetype="application/json")


@app.route("/getData", methods=["GET"])
def getData():
    endpoint = "getData"
    denied = checkauth(endpoint)
    if denied:
        return denied
    start = request.args.get("start")
    end = request.args.get("end")
    if start is None or end is None:
        return fail(endpoint, "start and end are mandatory")
    if not validdate(start) or not validdate(end):
        return fail(endpoint, "start and end must use the format YYYY-MM-DD HH:MM:SS")
    if start > end:
        return fail(endpoint, "start must be before end")
    sql = ("SELECT *, ST_AsText(`geo_point`) AS `geo` FROM `class_datapoints` "
           "WHERE `date_time` BETWEEN %s AND %s ORDER BY `date_time` LIMIT %s;")
    try:
        rows, sqltime = runquery(sql, (start, end, LIMIT))
    except Exception as e:
        return fail(endpoint, "database error: " + str(e))
    results = [cleanrow(r) for r in rows]
    res = {
        "code": 1,
        "msg": "ok",
        "req": endpoint,
        "sqltime": sqltime,
        "count": len(results),
        "results": results,
    }
    return reply(endpoint, res)


@app.route("/countInPolygon", methods=["GET"])
def countInPolygon():
    endpoint = "countInPolygon"
    denied = checkauth(endpoint)
    if denied:
        return denied
    polygon = request.args.get("polygon")
    if polygon is None or polygon.strip() == "":
        return fail(endpoint, "polygon is mandatory")
    points = []
    try:
        for pair in polygon.split(","):
            parts = pair.split()
            if len(parts) != 2:
                raise ValueError
            points.append((float(parts[0]), float(parts[1])))
    except ValueError:
        return fail(endpoint, "polygon must be a list of 'x y' points separated by commas")
    if points[0] != points[-1]:
        points.append(points[0])
    if len(points) < 4:
        return fail(endpoint, "polygon needs at least 3 distinct points")
    wkt = "Polygon((" + ",".join(f"{x} {y}" for x, y in points) + "))"
    sql = "SELECT COUNT(*) AS `count` FROM `class_datapoints` WHERE ST_Within(`geo_point`, ST_GeomFromText(%s, 0));"
    try:
        rows, sqltime = runquery(sql, (wkt,))
    except Exception as e:
        return fail(endpoint, "database error: " + str(e))
    res = {
        "code": 1,
        "msg": "ok",
        "req": endpoint,
        "sqltime": sqltime,
        "polygon": wkt,
        "count": int(rows[0]["count"]),
    }
    return reply(endpoint, res)


@app.route("/getAvgSpeedByFlight", methods=["GET"])
def getAvgSpeedByFlight():
    endpoint = "getAvgSpeedByFlight"
    denied = checkauth(endpoint)
    if denied:
        return denied
    start = request.args.get("start")
    end = request.args.get("end")
    if start is not None and not validdate(start):
        return fail(endpoint, "start must use the format YYYY-MM-DD HH:MM:SS")
    if end is not None and not validdate(end):
        return fail(endpoint, "end must use the format YYYY-MM-DD HH:MM:SS")
    if start is not None and end is not None and start > end:
        return fail(endpoint, "start must be before end")
    where = []
    params = []
    if start is not None:
        where.append("`date_time` >= %s")
        params.append(start)
    if end is not None:
        where.append("`date_time` <= %s")
        params.append(end)
    sql = "SELECT `flight_num`, AVG(`gs`) AS `avgspeed` FROM `class_datapoints`"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " GROUP BY `flight_num` ORDER BY `flight_num` LIMIT %s;"
    params.append(LIMIT)
    try:
        rows, sqltime = runquery(sql, tuple(params))
    except Exception as e:
        return fail(endpoint, "database error: " + str(e))
    results = [{"flight": r["flight_num"], "avgspeed": clean(r["avgspeed"])} for r in rows]
    res = {
        "code": 1,
        "msg": "ok",
        "req": endpoint,
        "sqltime": sqltime,
        "start": start,
        "end": end,
        "count": len(results),
        "results": results,
    }
    return reply(endpoint, res)


if __name__ == "__main__":
    setup()
    app.run(host="0.0.0.0", debug=True)
