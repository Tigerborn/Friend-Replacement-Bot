import os
import requests
from dotenv import load_dotenv

load_dotenv()


API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")


def get_current_weather_data(query):
    url = f"{API_URL}/current.json?key={API_KEY}&q={query}"
    response = requests.get(url)
    data = response.json()

    if "error" in data: #Handles the error
        message = "Sorry Couldn't find that location 💀"

    else:
        current_day = data['current']['last_updated']
        # Setting Time Format
        month = current_day[5:7]
        day = current_day[8:10]
        year = current_day[0:4]
        time_start = int(current_day[11:13])
        time_end = int(current_day[14:])
        status = "AM"
        if time_start >= 13:
            status = "PM"
            time_start -= 12

        date = f"{time_start}:{time_end} {status} on {month}/{day}/{year}"

        message = (f"Current Weather Report for {date} in {data['location']['name']}, {data['location']['country']}: \n"
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
        current_day = data['current']['last_updated']
        #Setting Time Format
        month = current_day[5:7]
        day = current_day[8:10]
        year = current_day[0:4]
        time_start = int(current_day[11:13])
        time_end = int(current_day[14:])
        status = "AM"
        if time_start >= 13:
            status = "PM"
            time_start -=12

        date = f"{time_start}:{time_end} {status} on {month}/{day}/{year}"

        message = (f"Current Weather Report for {date} in {data['location']['name']}, {data['location']['country']}: \n"
                   f"Temperature: {data['current']['temp_f']}°F ({data['current']['temp_c']}°C)\n"
                   f"Feels like: {data['current']['feelslike_f']}°F ({data['current']['feelslike_c']}°C)\n"
                   f"Humidity: {data['current']['humidity']}%\n"
                   f"Precipitation: {data['current']['precip_in']} in ({data['current']['precip_mm']} mm)\n"
                   f"Condition: {data['current']['condition']['text']}\n"
                   f"Windchill: {data['current']['windchill_f']}°F ({data['current']['windchill_c']}°C)\n"
                   f"Heat Index: {data['current']['heatindex_f']}°F ({data['current']['heatindex_c']}°C)\n"
                   f"Dew point: {data['current']['dewpoint_f']}°F ({data['current']['dewpoint_c']}°C)\n"
                   f"Wind Speed: {data['current']['wind_mph']} mph ({data['current']['wind_kph']} kph) {data['current']['wind_dir']}\n"
                   f"Wind Gust: {data['current']['gust_mph']} mph ({data['current']['gust_kph']} kph)\n"
                   f"Cloud Cover: {data['current']['cloud']}%\n"
                   f"UV Index: {data['current']['uv']}\n"
                   )
    return message

