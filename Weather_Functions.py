import os
import requests
from dotenv import load_dotenv
import math
import json
load_dotenv()


API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
def Time_Format_Fix(Time):
    #Gets a more readable Time format
    year = Time[0:4]
    month = Time[5:7]
    day = Time[8:10]
    time_start = int(Time[11:13])
    time_end = int(Time[14:16])
    if time_end == 0: #If the minutes of time is 0, adapt it to the modern time format of 00
        time_end = "00"
    status = "AM"
    if time_start >= 13:
        status = "PM"
        time_start -= 12
    date = f"{month}/{day}/{year} at {time_start}:{time_end} {status}"
    return date

def string_condenser(string: str):
    # Ensures the intended string is one char.
    if len(string) > 1:
        for x in string:
            if x.isalpha():
                string = x
                break
    return string


def latlon_to_tile(lat: float, lon: float, zoom: int):
    """
    Converts latitude & longitude into XYZ tile coordinates for Web Mercator.
    Returns (x, y) integers valid for WeatherAPI map URLs.
    """
    # Make sure values are in range
    lat = max(min(lat, 85.05112878), -85.05112878)  # Web Mercator limit
    lon = ((lon + 180) % 360) - 180  # wrap lon to [-180,180]

    n = 2.0 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.log(math.tan(math.radians(lat)) + (1 / math.cos(math.radians(lat)))) / math.pi) / 2.0 * n)
    return x, y


def weather(query, dump):
    url = f"{API_URL}/current.json?key={API_KEY}&q={query}"
    response = requests.get(url)
    data = response.json()

    if "error" in data: #Handles the error
        message = "Sorry Couldn't find that location 💀"

    else:
        current_day = data['current']['last_updated'] + "e" #Ensures proper indexing
        # Setting Time Format
        date = Time_Format_Fix(current_day)

        if dump == "Y":
            message = (f"Weather Report for {date} in {data['location']['name']}, {data['location']['country']}: \n"
                       f"Temperature: {data['current']['temp_f']}°F ({data['current']['temp_c']}°C)\n"
                       f"Feels like: {data['current']['feelslike_f']}°F ({data['current']['feelslike_c']}°C)\n"
                       f"Humidity: {data['current']['humidity']}%\n"
                       f"Precipitation: {data['current']['precip_in']} in ({data['current']['precip_mm']} mm)\n"
                       f"Condition: {data['current']['condition']['text']}\n"
                       f"Windchill: {data['current']['windchill_f']}°F ({data['current']['windchill_c']}°C)\n"
                       f"Heat Index: {data['current']['heatindex_f']}°F ({data['current']['heatindex_c']}°C)\n"
                       f"Dew point: {data['current']['dewpoint_f']}°F ({data['current']['dewpoint_c']}°C)\n"
                       f"Pressure: {data['current']['pressure_in']} in ({data['current']['pressure_mb']} mb)\n"
                       f"Wind Speed: {data['current']['wind_mph']} mph ({data['current']['wind_kph']} kph) {data['current']['wind_dir']}\n"
                       f"Wind Gust: {data['current']['gust_mph']} mph ({data['current']['gust_kph']} kph)\n"
                       f"Cloud Cover: {data['current']['cloud']}%\n"
                       f"UV Index: {data['current']['uv']}\n"
                       )
        else:
            message = (f"Weather Report for {date} in {data['location']['name']}, {data['location']['country']}: \n"
                       f"Temperature: {data['current']['temp_f']}°F ({data['current']['temp_c']}°C)\n"
                       f"Feels like: {data['current']['feelslike_f']}°F ({data['current']['feelslike_c']}°C)\n"
                       f"Humidity: {data['current']['humidity']}%\n"
                       f"Precipitation: {data['current']['precip_in']} in ({data['current']['precip_mm']} mm)\n"
                       f"Condition: {data['current']['condition']['text']}\n"
                       )
    return message


def emergency_status(query):
    url = f"{API_URL}/alerts.json?key={API_KEY}&q={query}&days=1&alerts=yes"
    response = requests.get(url)
    data = response.json()

    #Fix the time format and get related fields:
    Messages = []
    alerts = data.get("alerts",{}).get("alert",[])
    for alert in alerts:

        date_start = Time_Format_Fix(alert.get("effective"))
        date_end = Time_Format_Fix(alert.get("expires"))
        headline = alert.get("headline")
        msgtype = alert.get("msgtype")
        severity = alert.get("severity")
        urgency = alert.get("urgency")
        areas = alert.get("areas")
        category = alert.get("category")
        certainty = alert.get("certainty")
        event = alert.get("event")
        note = alert.get("note")
        desc = alert.get("desc")
        instruction = alert.get("instruction")

        message = (
            f"⚠️{event} - {severity}⚠️\n \n"
            f"{headline}\n \n"
            f"Affected areas: {areas}\n \n"
            f"From: {date_start} to: {date_end}\n \n"
            f"{desc} \n"
            f"{instruction}"
        )
        Messages.append(message)
    return Messages

def map_link(map_type,date,time,zoom,lat,long):
    if len(time) == 1: #Ensures if the hour is one digit it formats it as two.
        time = "0" + time

    #Convert lat and long to x,y
    x,y = latlon_to_tile(lat,long,zoom)
    url = f"https://weathermaps.weatherapi.com/{map_type}/tiles/{date}{time}/{zoom}/{x}/{y}.png"
    return url


def forecast(query, days, dump):
    #This function will return desired forcast and dump relevent info
    #Preparing the arrays that will be passed
    day = []
    hourly = []

    url = f"{API_URL}/forecast.json?key={API_KEY}&q={query}&days={days}"
    response = requests.get(url)
    data = response.json()
    forecast_days = data.get("forecast",{}).get("forecastday",[])
    #print(forecast_days)
    for day in forecast_days:
        print(day['date'])
        for hour in day.get ("hour", []):
            timestamp = Time_Format_Fix(hour['time'])
            print (timestamp)


#forecast(77345, 5, "N")
