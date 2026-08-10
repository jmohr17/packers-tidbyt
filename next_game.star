load("http.star", "http")
load("render.star", "render")

URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/gb/schedule?season=2026&seasontype=2"


def get_next_game():
    response = http.get(URL, ttl_seconds=900)

    if response.status_code != 200:
        fail("ESPN request failed")

    data = response.json()

    for event in data["events"]:
        competition = event["competitions"][0]
        status = competition.get("status", {}).get("type", {})

        if status.get("completed", False):
            continue

        competitors = competition["competitors"]

        packers = None
        opponent = None

        for team in competitors:
            if team["team"]["abbreviation"] == "GB":
                packers = team
            else:
                opponent = team

        return {
            "opponent": opponent["team"]["abbreviation"],
            "home_away": packers["homeAway"],
            "date": event["date"],
            "week": event["week"]["text"],
        }

    return None


def format_game_date(date_string):
    year = int(date_string[0:4])
    month = int(date_string[5:7])
    day = int(date_string[8:10])

    hour = int(date_string[11:13])
    minute = int(date_string[14:16])

    # ESPN supplies UTC.
    # August is daylight time in Central Time, so subtract 5 hours.
    hour = hour - 5

    if hour < 0:
        hour = hour + 24
        day = day - 1

    months = [
        "",
        "JAN",
        "FEB",
        "MAR",
        "APR",
        "MAY",
        "JUN",
        "JUL",
        "AUG",
        "SEP",
        "OCT",
        "NOV",
        "DEC",
    ]

    if hour == 0:
        display_hour = 12
    elif hour > 12:
        display_hour = hour - 12
    else:
        display_hour = hour

    if hour >= 12:
        am_pm = "PM"
    else:
        am_pm = "AM"

    date = months[month] + " " + str(day)
    if minute < 10:
        minute_text = "0" + str(minute)
    else:
     minute_text = str(minute)

    time = str(display_hour) + ":" + minute_text + " " + am_pm

    return date, time


def main():
    game = get_next_game()

    if game == None:
        return render.Root(
            child=render.Text(
                "NO GAME",
                color="FFB612",
            ),
        )

    location = "vs" if game["home_away"] == "home" else "@"

    date, game_time = format_game_date(game["date"])

    return render.Root(
     child=render.Column(
        children=[
            render.Text(
                "PACKERS",
                color="FFB612",
            ),
            render.Text(
                location + " " + game["opponent"],
                color="FFFFFF",
            ),
            render.Text(
                game["week"],
                color="FFFFFF",
            ),
            render.Text(
                date + "  " + game_time,
                color="FFFFFF",
            ),
        ],
    ),
)