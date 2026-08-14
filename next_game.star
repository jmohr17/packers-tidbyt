load("http.star", "http")
load("render.star", "render")


URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/gb/schedule?season=2026&seasontype=1"


def get_next_game():
    response = http.get(
        URL,
        ttl_seconds=900,
    )

    if response.status_code != 200:
        fail("ESPN request failed")

    data = response.json()

    upcoming_game = None
    recent_completed_game = None

    preseason_number = 0

    for event in data["events"]:
        competition = event["competitions"][0]
        status = competition.get("status", {}).get("type", {})

        # Every event returned by this URL is a preseason game.
        preseason_number = preseason_number + 1
        event["preseason_number"] = preseason_number

        if status.get("completed", False):
            recent_completed_game = event
        elif upcoming_game == None:
            upcoming_game = event

    if recent_completed_game != None:
        return recent_completed_game

    return upcoming_game


def get_score(team):
    score = team.get("score")

    if score == None:
        return None

    if score.get("displayValue") != None:
        return score["displayValue"]

    return str(score)


def main():
    event = get_next_game()

    if event == None:
        return render.Root(
            child=render.Text(
                "NO GAME",
                color="FFB612",
            ),
        )

    competition = event["competitions"][0]
    status = competition.get("status", {}).get("type", {})

    competitors = competition["competitors"]

    packers = None
    opponent = None

    for team in competitors:
        if team["team"]["abbreviation"] == "GB":
            packers = team
        else:
            opponent = team

    location = "vs"

    if packers["homeAway"] != "home":
        location = "@"

    packers_score = get_score(packers)
    opponent_score = get_score(opponent)

    children = [
        render.Text(
            "     PRE WK "
            + str(event["preseason_number"]),
            color="FFFFFF",
        ),
        render.Text(
            "     GB "
            + location
            + " "
            + opponent["team"]["abbreviation"],
            color="FFB612",
        ),
    ]

    if (
        packers_score != None
        and opponent_score != None
    ):
        result = "W"

        if int(packers_score) < int(opponent_score):
            result = "L"
        elif int(packers_score) == int(opponent_score):
            result = "T"

        children.append(
            render.Text("      "+
                packers_score
                + "     "
                + opponent_score,
                color="FFFFFF",
            ),
        )

    if status.get("completed", False):
        children.append(
            render.Text(
                "     FINAL"
                + " ("
                + result
                + ")",
                color="FFFFFF",
            ),
        )

    return render.Root(
        child=render.Column(
            children=children,
        ),
    )


main()