import fastapi
from fastapi.responses import Response
import uvicorn

from datetime import datetime, timedelta
from tempfile import SpooledTemporaryFile
import gzip
import os
import secrets
import aisdb
from aisdb import PostgresDBConn, DBQuery

app = fastapi.FastAPI()

MAX_CLIENT_MEMORY = 1024 * 1e6

db_args = dict(
    host=os.environ.get('AISDB_REST_DBHOST', 'fc00::17'),
    port=os.environ.get('AISDB_REST_DBPORT', 5431),
    user=os.environ.get('AISDB_REST_DBUSER', 'postgres'),
    password=os.environ.get('AISDB_REST_DBPASSWORD', 'devel'),
)

# verify database connection and prepare an example GET request
with PostgresDBConn(**db_args) as dbconn:
    db_rng = dbconn.db_daterange
    end = db_rng['end']
    start = max(db_rng['start'], db_rng['end'] - timedelta(days=31))
    default_query = {
        'start': int(datetime(start.year, start.month, start.day).timestamp()),
        'end': int(datetime(end.year, end.month, end.day).timestamp()),
        'xmin': -65,
        'xmax': -62,
        'ymin': 43,
        'ymax': 45,
    }


@app.get("/")
def read_root():
    # get args
    http_qry = dict(fastapi.Request().query_params)
    print(f'received request {http_qry} from client {fastapi.Request().client}')

    example_GET_qry = '<div id="base_uri" style="display: inline;" ></div>?' + '&'.join(
        f'{k}={v}' for k, v in default_query.items())

    # validate the request parameters
    need_keys = set(default_query.keys())
    recv_keys = set(http_qry.keys())
    missing = need_keys - recv_keys

    if len(recv_keys) == 0:
        return {
            "message": "AIS REST API",
            "description": "Query AIS message history using time and coordinate region to download a CSV data export.",
            "usage": "Begin request using a GET or POST request to this endpoint.",
            "parameters": {
                "xmin": "minimum longitude (decimal degrees)",
                "xmax": "maximum longitude (decimal degrees)",
                "ymin": "minimum latitude (decimal degrees)",
                "ymax": "maximum latitude (decimal degrees)",
                "start": "beginning timestamp (epoch seconds)",
                "end": "end timestamp (epoch seconds)"
            },
            "limitation": f"Requests are limited to 31 days at a time. Data is available from {db_rng['start']} to {db_rng['end']}.",
            "example_request": example_GET_qry
        }

    if len(missing) > 0:
        return {
            "error": f"missing keys from request: {missing}",
            "example": example_GET_qry
        }

    # convert parameter types from string
    http_qry['start'] = datetime.utcfromtimestamp(int(http_qry['start']))
    http_qry['end'] = datetime.utcfromtimestamp(int(http_qry['end']))
    for arg in ['xmin', 'xmax', 'ymin', 'ymax']:
        http_qry[arg] = float(http_qry[arg])

    # error handling for invalid requests
    if http_qry['end'] - http_qry['start'] > timedelta(days=31):
        return {"error": "A maximum of 31 days can be queried at once"}

    if http_qry['end'] <= http_qry['start']:
        return {"error": "end must occur after start"}

    if not (-180 <= http_qry['xmin'] < http_qry['xmax'] <= 180):
        return {"error": "invalid longitude range"}

    if not (-90 <= http_qry['ymin'] < http_qry['ymax'] <= 90):
        return fastapi.responses.JSONResponse(content={"error": "invalid longitude range"})

    with PostgresDBConn(**db_args) as dbconn:
        buf = SpooledTemporaryFile(max_size=MAX_CLIENT_MEMORY)

        dbqry = DBQuery(dbconn=dbconn,
                        callback=aisdb.sqlfcn_callbacks.in_bbox_time_validmmsi,
                        **http_qry).gen_qry(
            fcn=aisdb.sqlfcn.crawl_dynamic_static,
            verbose=False)

        tracks = aisdb.TrackGen(dbqry, decimate=0.0001)
        # csv_rows = aisdb.proc_util.tracks_csv(tracks)
        '''
        def generate(csv_rows):
            start_qry = next(csv_rows)
            yield ','.join(map(str, start_qry)) + '\n'
            yield ','.join(map(str, start_qry)) + '\n'
            for row in csv_rows:
                yield ','.join(map(str, row)) + '\n'

        lines = generate(csv_rows)
        # start query generation so that the DBConn object isnt garbage collected
        _ = next(lines)
        '''
        lines = aisdb.proc_util.write_csv(tracks, buf)
        buf.flush()

        download_name = f'ais_{http_qry["start"].date()}_{http_qry["end"].date()}.csv'
        buf.seek(0)
        count = sum(1 for line in buf)
        print(f'sending {count} rows to client {fastapi.Request().client}',
              flush=True)
        buf.seek(0)
        return Response(
            gzip.compress(buf.read(), compresslevel=9),
            mimetype='application/csv',
            headers={
                'Content-Disposition': f'attachment;filename={download_name}',
                'Content-Encoding': 'gzip',
                'Keep-Alive': 'timeout=0'
            },
        )
        try:
            pass
        except aisdb.track_gen.EmptyRowsException:
            buf.close()
            return Markup("No results found for query")
        except Exception as err:
            raise err


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
