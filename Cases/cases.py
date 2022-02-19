###############################################################################

# Copyright (C) 2022  Siddh Raman Pant

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# The online repository may be found at <github.com/covid-saarani/lipik>.

###############################################################################


# Import standard library dependencies.
import json
from typing import Any

# Import external dependencies.
import pendulum
import requests

# Import the main filling functions.
from .mohfw import parse_mohfw
from .mygov import parse_mygov


def set_yesterday_to_day_before(pretty: dict[str, Any]) -> None:
    """Example: 02nd Feb -> 1st Feb."""

    yesterday = pretty["internal"]["yesterday"].subtract(days=1)
    day_before_yesterday = yesterday.subtract(days=1)

    pretty["internal"]["yesterday"] = yesterday
    pretty["internal"]["day_before_yesterday"] = day_before_yesterday
    pretty["internal"]["old_filename"] = (
        "../saarani/Daily/"
        + day_before_yesterday.format("YYYY_MM_DD")
        + ".json"
    )

    pretty["timestamp"]["cases"]["date"] = yesterday.format("DD MMM YYYY")
# End of set_yesterday_to_day_before().


def fill_cases(pretty: dict[str, Any]) -> None:
    """
    Fetches data from MyGov and MoHFW, and fills in the `pretty` dict.

    If MyGov data is outdated, the internal bool is set to False, and MoHFW
    data is used.

    If current data is same as previous data, internal `yesterday` is
    decremented by 1.
    """
    mohfw = requests.get(pretty["internal"]["mohfw_cases"]).json()
    mygov = requests.get(pretty["internal"]["mygov_cases"]).json()

    # 0th is A&N Islands. Check total cases, it cannot decrease with time.
    if mygov["Total Confirmed cases"]["0"] < mohfw[0]["new_positive"]:
        # MyGov data is outdated compared to the MoHFW one.
        print("Using MoHFW data.")
        pretty["internal"]["use_mygov"] = False
        parse_mygov(pretty, mygov, fill_data=False)
        parse_mohfw(pretty, mohfw)
        return

    # else:
    # Parse MyGov data, and add reconciled death data from MoHFW data.
    print("Using MyGov data.")
    parse_mygov(pretty, mygov)
    parse_mohfw(pretty, mohfw, reconciliation_only=True)

    # Check if we have 2 day old data instead of 1 day old.

    try:
        with open(pretty["internal"]["old_filename"]) as f:
            old_data = json.load(f)  # Day before yesterday's data.

    except FileNotFoundError:
        # We don't have previous data, so can't figure out if we are indeed
        # setting data for correct date. So let's check for time and decide.

        # Stats usually come after 0830 IST for the prev day (we fetch hourly).
        # If we fetch before it then we are getting data of 2 days ago.
        now = pendulum.now("Asia/Kolkata")
        if now.hour < 8 or (now.hour == 8 and now.minute < 30):
            set_yesterday_to_day_before(pretty)

    else:
        if pretty["All"]["confirmed"] == old_data["All"]["confirmed"]:
            # Total cases yesterday == total cases day before yesterday.
            # This is impossible, and implies we have the latter.
            set_yesterday_to_day_before(pretty)
# End of fill_cases().


# End of file.
