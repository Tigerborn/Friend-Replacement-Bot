import os
from idlelib import query

import requests
from dotenv import load_dotenv
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


def get_current_weather_data(query):
    url = f"{API_URL}/current.json?key={API_KEY}&q={query}"
    response = requests.get(url)
    data = response.json()

    if "error" in data: #Handles the error
        message = "Sorry Couldn't find that location 💀"

    else:
        current_day = data['current']['last_updated'] + "e" #Ensures proper indexing
        # Setting Time Format
        date = Time_Format_Fix(current_day)

        message = (f"Weather Report for {date} in {data['location']['name']}, {data['location']['country']}: \n"
                   f"Temperature: {data['current']['temp_f']}°F ({data['current']['temp_c']}°C)\n"
                   f"Feels like: {data['current']['feelslike_f']}°F ({data['current']['feelslike_c']}°C)\n"
                   f"Humidity: {data['current']['humidity']}%\n"
                   f"Precipitation: {data['current']['precip_in']} in ({data['current']['precip_mm']} mm)\n"
                   f"Condition: {data['current']['condition']['text']}\n"
                   )
    return message


def get_current_weather_data_extend(query):
    url = f"{API_URL}/current.json?key={API_KEY}&q={query}"
    response = requests.get(url)
    data = response.json()

    if "error" in data: #Handles the error
        message = "Sorry! Couldn't find that location 💀"

    else:
        #Gets a more readable time format
        current_day = data['current']['last_updated'] + "e" #Ensures proper indexing
        date = Time_Format_Fix(current_day)

        #Displayes weather information for the region
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
    return message

def Check_Emergency_Status(query):
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

def Display_Map(query,date,time,zoom,x,y):
    url = f"https://weathermaps.weatherapi.com/{query}/tiles/{date}{time}/{zoom}/{x}/{y}.png"
    return url


