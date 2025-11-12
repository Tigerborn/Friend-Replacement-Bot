import os
import requests
from dotenv import load_dotenv
import math
from datetime import datetime, timedelta
import json
load_dotenv()


API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
def Time_Format_Fix(time):
    #Gets a more readable Time format
    year = time[0:4]
    month = time[5:7]
    day = time[8:10]
    time_start = int(time[11:13])
    time_end = int(time[14:16])
    if time_end == 0: #If the minutes of time is 0, adapt it to the modern time format of 00
        time_end = "00"
    status = "AM"
    if time_start == 0:
        time_start = 12

    elif time_start == 12:
        status = "PM"

    elif time_start >= 13:
        status = "PM"
        time_start -= 12
    date = f"{month}/{day}/{year} at {time_start}:{time_end} {status}"
    return date
def Date_Format_Fix(Date: str):
    #Returns Date in MM/DD/YYYY format
    year = Date[0:4]
    month = Date[5:7]
    day = Date[8:10]
    return f"{month}/{day}/{year}"

def get_date():
    #Gets current date in MM/DD/YYYY format
    now = datetime.now()
    date = now.strftime("%m/%d/%Y")
    return date

def get_future_date(days: int):
    #Gets the date of number of days from current date
    date = get_date()
    future_day = f"{(int(date[3:5]) + days)}"
    date = date[0:3] + future_day + date[5:]
    return date



def days_between(desired_date: str):
    #Gets the number of days between desired date and current date
    current_date = get_date()

    days_between = (int(desired_date[3:5]) - int(current_date[3:5]))
    return days_between + 1

def string_condenser(string: str):
    # Ensures the intended string is one char.
    if len(string) > 1:
        for x in string:
            if x.isalpha():
                string = x
                break
    return string


def latlon_to_tile(lat: float,
                   lon: float,
                   zoom: int
                   ):
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


def weather(query, alert, dump):
    url = f"{API_URL}/current.json?key={API_KEY}&q={query}"
    response = requests.get(url)
    data = response.json()

    if "error" in data: #Handles the error
        message = "Sorry Couldn't find that location 💀"

    else:
        current_day = data['current']['last_updated'] + "e" #Ensures proper indexing
        # Setting Time Format
        date = Time_Format_Fix(current_day)
        message = (f"_____________________________________________________________\n"
                   f"Weather Report for {date} in {data['location']['name']}, {data['location']['country']} \n"
                   f"_____________________________________________________________\n"
                   f"Temperature: {data['current']['temp_f']}°F ({data['current']['temp_c']}°C)\n"
                   f"Feels like: {data['current']['feelslike_f']}°F ({data['current']['feelslike_c']}°C)\n"
                   f"Condition: {data['current']['condition']['text']}\n"
                   f"Humidity: {data['current']['humidity']}%\n"
                   f"Precipitation: {data['current']['precip_in']} in ({data['current']['precip_mm']} mm)\n"
                   )
        if dump == "Y": #If dump is enabled, add this extra data the message
            message += (f"Windchill: {data['current']['windchill_f']}°F ({data['current']['windchill_c']}°C)\n"
                       f"Heat Index: {data['current']['heatindex_f']}°F ({data['current']['heatindex_c']}°C)\n"
                       f"Dew point: {data['current']['dewpoint_f']}°F ({data['current']['dewpoint_c']}°C)\n"
                       f"Pressure: {data['current']['pressure_in']} in ({data['current']['pressure_mb']} mb)\n"
                       f"Wind Speed: {data['current']['wind_mph']} mph ({data['current']['wind_kph']} kph) {data['current']['wind_dir']}\n"
                       f"Wind Gust: {data['current']['gust_mph']} mph ({data['current']['gust_kph']} kph)\n"
                       f"Cloud Cover: {data['current']['cloud']}%\n"
                       f"UV Index: {data['current']['uv']}\n"
                       )
        if alert == "Y":
            message += emergency_status(query)
    return message


def emergency_status(query,days: int = 1):
    url = f"{API_URL}/alerts.json?key={API_KEY}&q={query}&days={days}&alerts=yes"
    response = requests.get(url)
    data = response.json()

    #Fix the time format and get related fields:
    messages = []
    final = ""
    alerts = data.get("alerts",{}).get("alert",[])
    if not alerts:
        message = (f"_____________________________________________________________\n"
                   f"**There are no active alerts in your area** 😱😎\n"
                   f"_____________________________________________________________\n"
                   )
        messages.append(message)
    else:
        for alert in alerts:
            date_start = Time_Format_Fix(alert.get("effective"))
            date_end = Time_Format_Fix(alert.get("expires"))
            headline = alert.get("headline")
            severity = alert.get("severity")
            areas = alert.get("areas")
            event = alert.get("event")
            desc = alert.get("desc")
            instruction = alert.get("instruction")

            message = (
                f"_____________________________________________________________\n"
                f"⚠️**{event} - {severity}⚠️**\n \n"
                f"_____________________________________________________________\n"
                f"{headline}\n \n"
                f"Affected areas: {areas}\n \n"
                f"From: {date_start} to: {date_end}\n \n"
                f"{desc} \n"
                f"{instruction}"
                f"_____________________________________________________________\n"
            )
            messages.append(message)
    for m in messages:
        final += m
    return final

def map_link(map_type,date,time,zoom,lat,long):
    if len(time) == 1: #Ensures if the hour is one digit it formats it as two.
        time = "0" + time

    #Convert lat and long to x,y
    x,y = latlon_to_tile(lat,long,zoom)
    url = f"https://weathermaps.weatherapi.com/{map_type}/tiles/{date}{time}/{zoom}/{x}/{y}.png"
    return url


def forecast(query, date, daily, hourly, current_to_date, emergency, dump):
    #This function will return desired forcast and dump relevent info
    #Preparing the arrays that will be passed
    messages = []
    d = days_between(date)
    i = 0
    url = f"{API_URL}/forecast.json?key={API_KEY}&q={query}&days={d}"
    response = requests.get(url)
    data = response.json()
    forecast_days = data.get("forecast",{}).get("forecastday",[])
    final_message = ""
    if "error" in data: #Handles the error
        final_message = "Sorry Couldn't find that location 💀"
    else:
        message = f""
        for days in forecast_days:
            day = days["day"]
            astro = days.get("astro",{})
            if (current_to_date == "Y" or date == Date_Format_Fix(days['date']) and daily == "Y"): #If current
                message += (f"_____________________________________________________________\n"
                            f"🌡️**Forecast for {Date_Format_Fix(days['date'])}**🌡️ \n"
                            f"_____________________________________________________________\n"
                            f"Minimum Temperature: {day['mintemp_f']}°F ({day['mintemp_c']}°C)\n"
                            f"Maximum Temperature: {day['maxtemp_f']}°F ({day['maxtemp_c']}°C)\n"
                            f"Average Tempearture: {day['avgtemp_f']}°F ({day['avgtemp_c']}°C)\n"
                            f"Condition: {day['condition']['text']}\n"
                            f"Average Humidity: {day['avghumidity']}%\n"
                            f"Average Visibility: {day['avgvis_miles']} mi ({day['avgvis_km']} km)\n"
                            )


                if (day['daily_will_it_rain'] == 1):
                    message += (f"Chance of Rain: {day['daily_chance_of_rain']}%\n"
                               f"Total Precipitation: {day['totalprecip_in']} in ({day['totalprecip_mm']} mm)\n")
                if (day['daily_will_it_snow'] == 1):
                    message += (f"Chance of Snow: {day['daily_chance_of_snow']}%\n"
                               f"Total Snow: {day['totalsnow_cm']} cm\n")
                if dump == "Y":
                    message += (f"Maximum Wind Speed: {day['maxwind_mph']} mph ({day['maxwind_kph']} kph) \n"
                                f"UV index: {day['uv']}\n"
                                f"Sunrise: {astro['sunrise']}\n"
                                f"Sunset: {astro['sunset']}\n"
                                f"Moonrise: {astro['moonrise']}\n"
                                f"Moonset: {astro['moonset']}\n"
                                f"Moon Phase: {astro['moon_phase']}\n"
                                f"Moon Illumination: {astro['moon_illumination']}%\n"
                                )

            if hourly == "Y": #If hourly forecast is enabled
                for hour in days.get ("hour", []):
                    timestamp = f"{Time_Format_Fix(hour['time'])} \n"
                    message += timestamp
            message += f"_____________________________________________________________\n"
            i += 1
        if emergency == "Y":
            message += emergency_status(query,d)
    return message

#print(weather(77345, "Y", "Y"))
print(forecast(77345,"11/15/2025","N","Y","Y", "Y", "N"))