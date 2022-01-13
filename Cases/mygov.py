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
import copy
from typing import Any, Union

# Import external dependencies.
import pendulum


def parse_mygov(
    pretty: dict[str, Any],  # Formatted dict.
    mygov: dict[str, Union[str, dict[str, str]]],  # Dict directly from json.
    yesterday: pendulum.DateTime,
    fill_data: bool = True
) -> None:
    """
    Sets data according to the given JSON data fetched from MyGov.
    """

    # Get names of all states (Dicts are ordered in Python 3.7+).
    state_names = list(mygov["Name of State / UT"].values())

    # Make dict for each state, with its general information.
    for index, (state, abbr, hindi, helpline, donate) in enumerate(
        zip(
            state_names,
            mygov["abbreviation_code"].values(),
            mygov["states_name_hi"].values(),
            mygov["state_helpline"].values(),
            mygov["state_donation_url"].values()
        )
    ):
        # First do some potential cleaning of data and typos.
        if state == "Andaman and Nicobar":
            state += " Islands"
            state_names[index] += " Islands"
            mygov["states_name_hi"][str(index)] += " द्वीपसमूह"
        elif state == "Telengana":
            state = "Telangana"
            state_names[index] = "Telangana"

        pretty[state] = copy.deepcopy(pretty["All"])

        pretty[state]["abbr"] = abbr          # 2 letter abbreviation.
        pretty[state]["hindi"] = hindi        # Hindi name; Useful for l10n.
        pretty[state]["helpline"] = helpline  # State helpline for COVID.
        pretty[state]["donate"] = donate      # For donating to state funds.

    # If asked not to fill stats, we are done here.
    if not fill_data:
        return

    # Store timestamps.
    pretty["timestamp"]["cases"] = {
        "date": yesterday.format("DD MMM YYYY"),
        "as_on": mygov["as_on"],
        "last_updated_unix": mygov["updated_on"],
        "last_fetched_unix": round(pendulum.now().timestamp())
    }

    # For setting in national stats.
    national_confirmed = pretty["All"]["confirmed"]
    national_active = pretty["All"]["active"]
    national_recovered = pretty["All"]["recovered"]
    national_deaths = pretty["All"]["deaths"]

    # Add cases data to state dicts.
    for (
            state,
            confirmed, active, recovered, deaths,
            prev_confirmed, prev_active, prev_recovered, prev_deaths,
            new_confirmed, new_active, new_recovered, new_deaths
        ) in zip(
            state_names,

            map(int, mygov["Total Confirmed cases"].values()),
            map(int, mygov["Active"].values()),
            map(int, mygov["Cured/Discharged/Migrated"].values()),
            map(int, mygov["Death"].values()),

            map(int, mygov["last_confirmed_covid_cases"].values()),
            map(int, mygov["last_active_covid_cases"].values()),
            map(int, mygov["last_cured_discharged"].values()),
            map(int, mygov["last_death"].values()),

            map(int, mygov["diff_confirmed_covid_cases"].values()),
            map(int, mygov["diff_active_covid_cases"].values()),
            map(int, mygov["diff_cured_discharged"].values()),
            map(int, mygov["diff_death"].values())
    ):
        # Each stat has case counts : current day, previous day, and new cases.
        # Ratio is calculated and stored for all, except confirmed (obviously).

        state_confirmed = pretty[state]["confirmed"]
        state_confirmed["current"] = confirmed
        state_confirmed["previous"] = prev_confirmed
        state_confirmed["new"] = new_confirmed

        state_active = pretty[state]["active"]
        state_active["current"] = active
        state_active["previous"] = prev_active
        state_active["new"] = new_active
        state_active["ratio_pc"] = round((100 * active) / confirmed, 5)

        state_recovered = pretty[state]["recovered"]
        state_recovered["current"] = recovered
        state_recovered["previous"] = prev_recovered
        state_recovered["new"] = new_recovered
        state_recovered["ratio_pc"] = round((100 * recovered) / confirmed, 5)

        state_deaths = pretty[state]["deaths"]
        state_deaths["current"] = deaths
        state_deaths["previous"] = prev_deaths
        state_deaths["new"] = new_deaths
        state_deaths["ratio_pc"] = round((100 * deaths) / confirmed, 5)

        # Add to the total national count.

        national_confirmed["current"] += confirmed
        national_confirmed["previous"] += prev_confirmed
        national_confirmed["new"] += new_confirmed

        national_active["current"] += active
        national_active["previous"] += prev_active
        national_active["new"] += new_active

        national_recovered["current"] += recovered
        national_recovered["previous"] += prev_recovered
        national_recovered["new"] += new_recovered

        national_deaths["current"] += deaths
        national_deaths["previous"] += prev_deaths
        national_deaths["new"] += new_deaths
    # End of for loop.

    # Calculate ratios for the total national counts, with precision of 5.
    national_total = national_confirmed["current"]
    national_active["ratio_pc"] = round(
        (100 * national_active["current"]) / national_total, 5
    )
    national_recovered["ratio_pc"] = round(
        (100 * national_recovered["current"]) / national_total, 5
    )
    national_deaths["ratio_pc"] = round(
        (100 * national_deaths["current"]) / national_total, 5
    )
# End of parse_mygov()


# End of file.
