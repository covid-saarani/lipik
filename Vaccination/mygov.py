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


def set_all_doses(age_data: dict[str, Any]) -> None:
    """Populate all_doses dict."""

    age_data["all_doses"]["total"] = (
        age_data["1st_dose"]["total"]
        + age_data["2nd_dose"]["total"]
        + age_data["3rd_dose"]["total"]
    )

    age_data["all_doses"]["new"] = (
        age_data["1st_dose"]["new"]
        + age_data["2nd_dose"]["new"]
        + age_data["3rd_dose"]["new"]
    )
# End of set_all_doses().


def set_data_from_keys(
    state_stats: dict[str, Any],
    data: dict[str, Any],

    # Total
    key_curr_dose_all: str, key_prev_dose_all: str,

    # 18+
    key_curr_dose1_18: str, key_prev_dose1_18: str,
    key_curr_dose2_18: str, key_prev_dose2_18: str,
    key_curr_dose3_18: str, key_prev_dose3_18: str,

    # 60+
    key_curr_dose3_60: str, key_prev_dose3_60: str,

    # 15-15
    key_curr_dose1_15: str, key_prev_dose1_15: str,
    key_curr_dose2_15: str, key_prev_dose2_15: str,

    # 12-14
    key_curr_dose1_12: str, key_prev_dose1_12: str,
    key_curr_dose2_12: str, key_prev_dose2_12: str,

) -> None:
    """
    Given keys, set data.
    """
    state_all = state_stats["all_ages"]
    state_18 = state_stats["18+"]
    state_15 = state_stats["15-18"]
    state_12 = state_stats["12-14"]

    # Helper function.
    def get_data(key: str) -> int:
        return int(data[key])
    # End of get_data().

    ###########################################################################

    # Set 18+ stats.

    state_18["1st_dose"]["total"] = get_data(key_curr_dose1_18)
    state_18["1st_dose"]["new"] = (
        get_data(key_curr_dose1_18) - get_data(key_prev_dose1_18)
    )

    state_18["2nd_dose"]["total"] = get_data(key_curr_dose2_18)
    state_18["2nd_dose"]["new"] = (
        get_data(key_curr_dose2_18) - get_data(key_prev_dose2_18)
    )

    state_18["3rd_dose"]["total"] = (
        get_data(key_curr_dose3_18) + get_data(key_curr_dose3_60)
    )
    state_18["3rd_dose"]["new"] = (
        get_data(key_curr_dose3_18) + get_data(key_curr_dose3_60)
        - get_data(key_prev_dose3_18) - get_data(key_prev_dose3_60)
    )

    set_all_doses(state_18)

    ###########################################################################

    # Now set 15-18 stats.

    state_15["1st_dose"]["total"] = get_data(key_curr_dose1_15)
    state_15["1st_dose"]["new"] = (
        get_data(key_curr_dose1_15) - get_data(key_prev_dose1_15)
    )

    state_15["2nd_dose"]["total"] = get_data(key_curr_dose2_15)
    state_15["2nd_dose"]["new"] = (
        get_data(key_curr_dose2_15) - get_data(key_prev_dose2_15)
    )

    set_all_doses(state_15)

    ###########################################################################

    # Now set 12-14 stats.

    state_12["1st_dose"]["total"] = get_data(key_curr_dose1_12)
    state_12["1st_dose"]["new"] = (
        get_data(key_curr_dose1_12) - get_data(key_prev_dose1_12)
    )

    state_12["2nd_dose"]["total"] = get_data(key_curr_dose2_12)
    state_12["2nd_dose"]["new"] = (
        get_data(key_curr_dose2_12) - get_data(key_prev_dose2_12)
    )

    set_all_doses(state_12)

    ###########################################################################

    # Now set all ages data.

    # Helper function
    def add_data_all(dose_key: str, stat_key: str) -> int:
        return (
            state_18[dose_key][stat_key]
            + state_15[dose_key][stat_key]
            + state_12[dose_key][stat_key]
        )
    # End of add_data_all().

    state_all["1st_dose"]["total"] = add_data_all("1st_dose", "total")
    state_all["1st_dose"]["new"] = add_data_all("1st_dose", "new")

    state_all["2nd_dose"]["total"] = add_data_all("2nd_dose", "total")
    state_all["2nd_dose"]["new"] = add_data_all("2nd_dose", "new")

    state_all["3rd_dose"]["total"] = add_data_all("3rd_dose", "total")
    state_all["3rd_dose"]["new"] = add_data_all("3rd_dose", "new")

    set_all_doses(state_all)

    ###########################################################################

    # Validate

    all_total = get_data(key_curr_dose_all)
    all_new = all_total - get_data(key_prev_dose_all)

    assert all_total == state_all["all_doses"]["total"]
    assert all_new == state_all["all_doses"]["new"]
# End of set_data_from_keys()


def fill_mygov_data(pretty: dict[str, Any]) -> None:
    """Get state vaccination stats from MyGov JSON, and fill it in `pretty`."""

    stats = requests.get(pretty["internal"]["mygov_vaccination"]).json()

    # Set timestamp.
    pretty["timestamp"]["vaccination"] = {
        "primary_source": "mygov",
        "date": pendulum.parse(stats["day"]).format("DD MMM YYYY"),
        "as_on": stats["updated_on"],
        "last_fetched_unix": round(pendulum.now().timestamp())
    }

    # Set national data
    set_data_from_keys(
        pretty["All"]["vaccination"], stats,

        # Total
        "india_total_doses", "india_last_total_doses",

        # 18+
        "india_dose1", "india_last_dose1",
        "india_dose2", "india_last_dose2",
        "india_dose3", "india_last_dose3",

        # 60+
        "precaution_dose", "india_last_precaution_dose",

        # 15 - 18
        "india_dose1_15_18", "india_last_dose1_15_18",
        "india_dose2_15_18", "india_last_dose2_15_18",

        # 12 - 14
        "india_dose1_12_14", "india_last_dose1_12_14",
        "india_dose2_12_14", "india_last_dose2_12_14"
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

            # Total
            "total_doses", "last_total_doses",

            # 18+
            "dose1", "last_dose1",
            "dose2", "last_dose2",
            "dose3", "last_dose3",

            # 60+
            "precaution_dose", "last_precaution_dose",

            # 15 - 18
            "dose1_15_18", "last_dose1_15_18",
            "dose2_15_18", "last_dose2_15_18",

            # 12 - 14
            "dose1_12_14", "last_dose1_12_14",
            "dose2_12_14", "last_dose2_12_14"
        )
# End of fill_mygov_data()


# End of file.
