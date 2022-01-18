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
from typing import Any

# Import external dependencies.
import pendulum

# Import helper function.
from Helpers.fuzzy_find_name import find_name


def parse_mohfw(
    pretty: dict[str, Any],  # Formatted dict.
    mohfw: list[dict[str, str]],  # Dict directly from json.
    yesterday: pendulum.DateTime,
    reconciliation_only: bool = False  # If only to fill reconciliation data.
) -> None:
    """
    Sets data according to the given JSON data fetched from MoHFW.
    """
    pretty_states_set = set(pretty.keys()) - {"All", "internal", "timestamp"}
    pretty_states_tuple = tuple(pretty_states_set)

    for data in mohfw:
        if data["state_name"] in pretty_states_set:
            state = data["state_name"]
        elif not data["state_name"] and data["sno"] == "11111":
            # National stats.
            state = "All"
        else:
            state = find_name(data["state_name"], pretty_states_tuple)

        if reconciled := data["death_reconsille"]:  # If not an empty string.
            pretty[state]["deaths"]["reconciled"] = int(reconciled)

        if reconciliation_only:
            continue

        # Each stat has case counts : current day, previous day, and new cases.
        # Ratio is calculated and stored for all, except confirmed (obviously).

        # Confirmed cases:

        state_confirmed = pretty[state]["confirmed"]
        confirmed = int(data["new_positive"] or 0)
        prev_confirmed = int(data["positive"] or 0)
        delta_confirmed = confirmed - prev_confirmed

        state_confirmed["current"] = confirmed
        state_confirmed["previous"] = prev_confirmed
        state_confirmed["delta"] = delta_confirmed

        # Active cases:

        state_active = pretty[state]["active"]
        active = int(data["new_active"] or 0)
        prev_active = int(data["active"] or 0)
        delta_active = active - prev_active

        state_active["current"] = active
        state_active["previous"] = prev_active
        state_active["delta"] = delta_active
        state_active["ratio_pc"] = round((100 * active) / confirmed, 5)

        # Recovered cases:

        state_recovered = pretty[state]["recovered"]
        recovered = int(data["new_cured"] or 0)
        prev_recovered = int(data["cured"] or 0)
        delta_recovered = recovered - prev_recovered

        state_recovered["current"] = recovered
        state_recovered["previous"] = prev_recovered
        state_recovered["delta"] = delta_recovered
        state_recovered["ratio_pc"] = round((100 * recovered) / confirmed, 5)

        # Deaths:

        state_deaths = pretty[state]["deaths"]
        deaths = int(data["new_death"] or 0)
        prev_deaths = int(data["death"] or 0)
        delta_deaths = int(data["total"] or 0)

        state_deaths["current"] = deaths
        state_deaths["previous"] = prev_deaths
        state_deaths["delta"] = delta_deaths
        state_deaths["ratio_pc"] = round((100 * deaths) / confirmed, 5)
    # End of for loop.

    if reconciliation_only:
        return

    # Store timestamps.
    pretty["timestamp"]["cases"] = {
        "date": yesterday.format("DD MMM YYYY"),
        "as_on": pendulum.now("Asia/Kolkata").format("DD MMM YYYY, HH:mm zz"),
        "last_fetched_unix": round(pendulum.now().timestamp())
    }
# End of parse_mohfw()


# End of file.
