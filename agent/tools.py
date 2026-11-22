from datetime import datetime
import httpx


CALENDAR_TOOL = {
    "type": "function",
    "function": {
        "name": "get_calendar_day",
        "description": (
            "Returns all appointments of one day from the user's calendar "
            "(start, end, title, location). Use it for any question about "
            "what is scheduled on a specific date."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "The day to look up, format YYYY-MM-DD, e.g. 2026-10-29",
                },
            },
            "required": ["date"],
        },
    },
}

WEATHER_TOOL = {
    "type": "function",
    "function":{
        "name": "get_weather",
        "description":(
            "Returns the weather forecast of one day for one city from the weather database "
            "(e.g. temperature, conditions, rain probability). Use it for any question about "
            "the weather on a specific day or whether an umbrella is needed. "
            "If no data is found, this does not mean that it will not rain."
        ),
        "parameters": {
            "type": "object",
            "properties":{
                "date": {
                    "type": "string",
                    "description": "The day to look up, format YYYY-MM-DD, e.g. 2026-10-29",
                },
                "city": {
                    "type": "string",
                                        "description": "City name in its local spelling, e.g. Ulm or München (not Munich)",
                }
            },
            "required": ["date","city"],
        },
    },
}

TRAIN_TOOL = {
    "type": "function",
    "function": {
        "name": "get_train_connection",
        "description":(
            "Returns the train connections of one day from one city to another from the "
            "train connection database (departure, arrival, train, changes, price). "
            "Use it for any question about how to travel from one city to another. "
            "The direction matters: from A to B is a different route than from B to A. "
            "If no data is found, this does not mean that no trains run."
            ),
        "parameters": {
            "type": "object",
            "properties":{
                "date": {
                    "type": "string",
                    "description": "The day to look up, format YYYY-MM-DD, e.g. 2026-10-29",
                },
                "start_location":{
                    "type": "string",
                    "description": "Departure city in its local spelling, e.g. Ulm or München (not Munich)"

                },
                "end_location": {
                    "type": "string",
                    "description": "Destination city in its local spelling, e.g. Ulm or München (not Munich)"

                }
            },
            "required": ["date", "start_location", "end_location"],
        },
    },
}

def check_date_format(date):
    ret = False
    try: 
        datetime.strptime(date, '%Y-%m-%d')
        ret = True
    except ValueError:
        ret = False

    return ret

def to_city_code(city):
    code = city.strip().lower()
    for umlaut, replacement in (('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'), ('ß', 'ss')):
        code = code.replace(umlaut, replacement)
    return code

def handle_httpx_response(response, what):
    if response.status_code == 404:
        ret = {'found': False, 'note': f'no data available for this {what}'}
    else:
        response.raise_for_status()   # 200 → continues; 403, 500, ... → raises httpx.HTTPStatusError
        ret = {'found': True, 'data': response.json()}

    return ret


def get_weather(date: str, city: str, data_base_url: str) -> dict:
    correct_format = check_date_format(date)

    if correct_format:
        url = f'{data_base_url}/weather/{to_city_code(city)}/{date}.json'
        response = httpx.get(url)
        ret = handle_httpx_response(response, 'city and day')
    else:
        ret = {'error': 'date must be YYYY-MM-DD'}

    return ret

def get_train_connection(date: str, start_location: str, end_location: str, data_base_url: str) -> dict:
    correct_format = check_date_format(date)

    if correct_format:
        url = f'{data_base_url}/transit/{to_city_code(start_location)}/{to_city_code(end_location)}/{date}.json'
        response = httpx.get(url)
        ret = handle_httpx_response(response, 'route and day')
    else:
        ret = {'error': 'date must be YYYY-MM-DD'}

    return ret


def get_calendar_day(date: str, data_base_url: str) -> dict:
    ret = ''

    correct_format = check_date_format(date)

    if correct_format:
        url = f'{data_base_url}/calendar/{date}.json'
        response = httpx.get(url)
        ret = handle_httpx_response(response, 'day')
    else:
        ret = {'error': 'date must be YYYY-MM-DD'}

    return ret