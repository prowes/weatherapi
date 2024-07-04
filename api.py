# before launching, add an API key to the environment variables list
# to launch, in command line run, for example:
# python .\api.py 60.24, 24.66, "gfs", weather.db, --parameters "temp", "rh"
import argparse
import datetime
import json
import numpy
import os
import requests
import sqlite3

parser = argparse.ArgumentParser(description="This program takes the latest weather values and compares them with the database ones.")
parser.add_argument("lat", help="Please specify latitude (for example 60.24")
parser.add_argument("lon", help="Please specity longtitude (for example 24.66).")
parser.add_argument("model", help="Please specify a model (for example, 'gfs', see API docs for details.")
parser.add_argument("db_file_name", help="Please specify a name of the database file you would like to use, for example 'weather.db'")
parser.add_argument("--parameters", nargs="*", help="Please specify parameters you would like to have in a list, for example ['temp', 'rh']")

args=parser.parse_args()

WINDY_URL = "https://api.windy.com/api/point-forecast/v2"
API_KEY = os.environ["WINDY_API_KEY"]
QUERY = {
    "lat": args.lat,
    "lon": args.lon,
    "model": args.model,
    "parameters": args.parameters,
    "key": API_KEY
}
DATABASE_NAME = args.db_file_name


def get_data():
    x = requests.post(WINDY_URL, json = QUERY)
    assert x.status_code == 200, f"Failed to fetch data, server responded with {x.status_code}"
    response = x.text
    response_from_windy_json = json.loads(response)
    return response_from_windy_json


def preprocess_data(response_from_windy_json, cur):
    times = response_from_windy_json["ts"]
    times = list(map(lambda x: x // 1000, times))  # milliseconds -> minutes
    temp_surface = response_from_windy_json["temp-surface"]
    temp_surface = list(map(lambda x: float(round(x, 2)), temp_surface))  # we don't need 8 symbols
    humid = response_from_windy_json["rh-surface"]
    humid = list(map(lambda x: float(round(x, 2)), humid))  # we don't need 8 symbols
    return times, temp_surface, humid


def put_data_to_db(times, temp_surface, humid):
    cur.execute("CREATE TABLE IF NOT EXISTS historical_weather(date, temp_surface, humidity)")
    query_to_put_histo_data = "INSERT INTO historical_weather VALUES"
    i = 1  # the 0th element is current data so it is omitted
    while i < len(times):
        query_to_put_histo_data += f"({times[i]},{temp_surface[i]},{humid[i]}),"
        i += 1
    cur.execute(query_to_put_histo_data[:-1])

def compare_last_value_with_hist(current_value, characteristic):
    cur.execute(f"SELECT {characteristic} FROM historical_weather")
    historical_values = cur.fetchall()
    median_hist_value = round(numpy.nanmedian(historical_values), 2)
    mean_hist_value = round(numpy.nanmean(historical_values), 2)
    print(f"Current value of {characteristic} is {current_value}, median is {median_hist_value}, mean is {mean_hist_value}")

    surfaces_mean = numpy.nanmean(historical_values)
    stand_dev = numpy.nanstd(historical_values)
    threshold = 2  # how many stds is considered as significant (2 is a common practice)
    upper_border = surfaces_mean + threshold * stand_dev
    lower_border = surfaces_mean - threshold * stand_dev
    if lower_border <= current_value <= upper_border:
        print(f"The current {characteristic} does not deviate that much")
    elif current_value > upper_border:
        print(f"The current {characteristic} deviates, it is way too high")
    elif current_value < lower_border:
        print(f"The current {characteristic} deviates, it is way too low")

response_from_windy_json = get_data()
con = sqlite3.connect(DATABASE_NAME)
cur = con.cursor()
times, temp_surface, humid = preprocess_data(response_from_windy_json, cur)
put_data_to_db(times, temp_surface, humid)
con.commit()

actual_surface_value = temp_surface[0]
print("Report:")
compare_last_value_with_hist(actual_surface_value, "temp_surface")
actual_humid_value = humid[0]
compare_last_value_with_hist(actual_humid_value, "humidity")
con.close()
