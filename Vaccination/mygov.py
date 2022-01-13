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
import requests

# Import helper function.
from Helpers.fuzzy_find_name import find_name


def set_data_from_keys(
    state_stats: dict[str, Any],
    data: dict[str, Any],

    key_curr_dose1_all: str,
    key_prev_dose1_all: str,

    key_curr_dose2_all: str,
    key_prev_dose2_all: str,

    key_curr_dose3_all: str,
    key_prev_dose3_all: str,

    key_curr_all_all: str,
    key_prev_all_all: str,

    key_curr_dose1_15: str,
    key_prev_dose1_15: str
) -> None:
    """
    Give keys, set data.
    """

    # Set stats for total / all ages.
    state_all = state_stats["all_ages"]

    state_all["1st_dose"]["total"] = int(data[key_curr_dose1_all])
    state_all["1st_dose"]["new"] = (int(data[key_curr_dose1_all])
                                    - int(data[key_prev_dose1_all]))

    state_all["2nd_dose"]["total"] = int(data[key_curr_dose2_all])
    state_all["2nd_dose"]["new"] = (int(data[key_curr_dose2_all])
                                    - int(data[key_prev_dose2_all]))

    state_all["3rd_dose"]["total"] = int(data[key_curr_dose3_all])
    state_all["3rd_dose"]["new"] = (int(data[key_curr_dose3_all])
                                    - int(data[key_prev_dose3_all]))

    state_all["all_doses"]["total"] = int(data[key_curr_all_all])
    state_all["all_doses"]["new"] = (int(data[key_curr_all_all])
                                     - int(data[key_prev_all_all]))

    # Set national 15-18 stats.
    state_15 = state_stats["15-18"]

    state_15["1st_dose"]["total"] = int(data[key_curr_dose1_15])
    state_15["1st_dose"]["new"] = (int(data[key_curr_dose1_15])
                                   - int(data[key_prev_dose1_15]))

    # As of 12th January, for 15-18 there is only 1 dose.
    state_15["all_doses"]["total"] = state_15["1st_dose"]["total"]
    state_15["all_doses"]["new"] = state_15["1st_dose"]["new"]

    # Set stats for 18+ age group. 18+ = Total - (15 to 18)
    state_18 = state_stats["18+"]

    state_18["1st_dose"]["total"] = (state_all["1st_dose"]["total"]
                                     - state_15["1st_dose"]["total"])
    state_18["1st_dose"]["new"] = (state_all["1st_dose"]["new"]
                                   - state_15["1st_dose"]["new"])

    state_18["2nd_dose"]["total"] = (state_all["2nd_dose"]["total"]
                                     - state_15["2nd_dose"]["total"])
    state_18["2nd_dose"]["new"] = (state_all["2nd_dose"]["new"]
                                   - state_15["2nd_dose"]["new"])

    state_18["3rd_dose"]["total"] = (state_all["3rd_dose"]["total"]
                                     - state_15["3rd_dose"]["total"])
    state_18["3rd_dose"]["new"] = (state_all["3rd_dose"]["new"]
                                   - state_15["3rd_dose"]["new"])

    state_18["all_doses"]["total"] = (state_all["all_doses"]["total"]
                                      - state_15["all_doses"]["total"])
    state_18["all_doses"]["new"] = (state_all["all_doses"]["new"]
                                    - state_15["all_doses"]["new"])
# End of set_data_from_keys()


def fill_mygov_data(pretty: dict[str, Any]) -> None:
    """Get state vaccination stats from MyGov JSON, and fill it in `pretty`."""

    stats = requests.get(pretty["internal"]["mygov_vaccination"]).json()

    # Set timestamp.
    pretty["timestamp"]["vaccination"] = {
        "date": pendulum.parse(stats["day"]).format("DD MMM YYYY"),
        "as_on": pendulum.now("Asia/Kolkata").format("DD MMM YYYY, HH:mm zz"),
        "last_fetched_unix": round(pendulum.now().timestamp())
    }

    # Set national data
    set_data_from_keys(
        pretty["All"]["vaccination"], stats,
        "india_dose1", "india_last_dose1",
        "india_dose2", "india_last_dose2",
        "precaution_dose", "india_last_precaution_dose",
        "india_total_doses", "india_last_total_doses",
        "india_dose1_15_18", "india_last_dose1_15_18"
    )

    # Now set state data.

    pretty_states_set = set(pretty.keys()) - {"All", "internal", "timestamp"}
    pretty_states_tuple = tuple(pretty_states_set)

    for data in stats["vacc_st_data"]:
        if data["st_name"] in pretty_states_set:
            state = data["st_name"]
        else:
            state = find_name(data["st_name"], pretty_states_tuple)

        set_data_from_keys(
            pretty[state]["vaccination"], data,
            "dose1", "last_dose1",
            "dose2", "last_dose2",
            "precaution_dose", "last_precaution_dose",
            "total_doses", "last_total_doses",
            "dose1_15_18", "last_dose1_15_18"
        )
# End of fill_mygov_data()


# End of file.
