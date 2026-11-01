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


def handle_httpx_response(response, date):
    ret = ""
   
    if response.status_code == 404:
        ret = {'date': date, 'events': [], 'found': False}
    else:
        response.raise_for_status()   # 200 → continues; 403, 500, ... → raises httpx.HTTPStatusError

        ret = {"date": date, "found": True, "events": response.json()["events"]}

    return ret


def get_calendar_day(date: str, data_base_url: str) -> dict:
    ret = ''
    try: 
        datetime.strptime(date, '%Y-%m-%d')
        correct_format = True
    except ValueError:
        correct_format = False

    if correct_format:
        url = f'{data_base_url}/calendar/{date}.json'
        response = httpx.get(url)
        ret = handle_httpx_response(response, date)
    else:
        ret = {'error': 'date must be YYYY-MM-DD'}

    return ret