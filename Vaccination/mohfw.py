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
import locale
from tempfile import NamedTemporaryFile
from typing import Any

# Import external dependencies.
import camelot
import pandas
import pendulum
import requests

# Import helper function.
from Helpers.fuzzy_find_name import find_name


class InvalidPdfException(ValueError):
    """Raised when the parsed PDF data isn't in the format we expect."""
    pass
# End of InvalidPdfException.


# Set the locale
locale.setlocale(locale.LC_ALL, 'en_IN')


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


def set_all_ages(vaccination_dict: dict[str, Any]) -> None:
    """Populate all_ages dict."""

    state_18 = vaccination_dict["18+"]
    state_15 = vaccination_dict["15-18"]
    state_12 = vaccination_dict["12-14"]
    state_all = vaccination_dict["all_ages"]

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
# End of set_all_ages()


def str_to_int(num_str: str) -> int:
    """Convert string with commas, dashes, etc. to integer."""
    num_str = num_str.strip().replace("-", "")
    if num_str:
        return locale.atoi(num_str)
    else:
        return 0  # Empty string => 0
# End of str_to_int()


def fill_mohfw_data(pretty: dict[str, Any]) -> None:
    """Get state vaccination stats from MoHFW PDF, and fill it in `pretty`."""

    pdf = NamedTemporaryFile(suffix=".pdf")
    pdf.write(requests.get(pretty["internal"]["mohfw_vaccination"]).content)

    # Parse the table from the pdf. Linux needed for using an open file.
    tables = camelot.read_pdf(pdf.name, backend="poppler")
    pdf.close()  # We no longer need it. Also will delete the same.

    # Make sure we have tables parsed in the expected format.
    # See the example CSV file for the expected format.

    if len(tables) != 2:
        raise InvalidPdfException("There must be 2 tables.")

    if 0 < tables[0].accuracy < 95 or 0 < tables[1].accuracy < 90:
        print(f"National table accuracy = {tables[0].accuracy}%")
        print(f"State table accuracy = {tables[1].accuracy}%")
        raise InvalidPdfException("Cannot detect the tables accurately.")

    national_table = tables[0].df
    states_table = tables[1].df

    # Check if state table is good.
    if len(states_table) != 41 or len(states_table.columns) != 11:
        print(states_table.to_string())  # For logging in CI.
        raise InvalidPdfException("State-wise vaccination stats "
                                  "not parsed correctly.")

    # Check if national table is good.
    if not (
        len(national_table) == 5
        and len(national_table.columns) == 6

        # 18+ 1st and 2nd dose
        and national_table[1][1] == "18+ Population"
        and national_table[1][2].count("\n") == 1       # 1st Dose \n2nd Dose
        and national_table[1][3].count("\n") == 1       # Numbers of doses.
        and national_table[1][4].count("\n") in (3, 4)  # Last 24 hours stat.

        # 15-18 1st and 2nd dose
        and national_table[2][1] == "15-18 Years"
        and national_table[2][2].count("\n") == 1  # Same as above...
        and national_table[2][3].count("\n") == 1
        and national_table[2][4].count("\n") in (3, 4)

        # 12-14 1st and 2nd dose
        and national_table[3][1] == "12-14 Years"
        and national_table[3][2].count("\n") == 1
        and national_table[3][3].count("\n") == 1
        and national_table[3][4].count("\n") in (3, 4)

        # 3rd dose (18+, 60+/worker)      "60+ Years, \n18-59 Years \nHCW, FLW"
        and national_table[4][1] == "Precaution Dose"
        and national_table[4][2].count("\n") == 2  # (The string above.)
        and national_table[4][3].count("\n") == 1
        and national_table[4][4].count("\n") in (3, 4)

        and national_table[5][0] == "Total Doses"
        and national_table[5][3].count("\n") == 0  # Number of total doses.
        and national_table[5][4].count("\n") == 1  # Last 24 hours stat.
    ):
        print(national_table.to_string())  # For logging in CI.
        raise InvalidPdfException("National vaccination stats "
                                  "not parsed correctly.")

    # Now, set national stats.

    national_18 = pretty["All"]["vaccination"]["18+"]
    national_15 = pretty["All"]["vaccination"]["15-18"]
    national_12 = pretty["All"]["vaccination"]["12-14"]

    ###########################################################################

    # For 18+ 1st and 2nd doses.

    dose_1, dose_2 = national_table[1][3].split()
    new_dose_1, new_dose_2 = [i[1:] for i in national_table[1][4].split()
                              if i[0] == "("]

    national_18["1st_dose"]["total"] = str_to_int(dose_1)
    national_18["1st_dose"]["new"] = str_to_int(new_dose_1)

    national_18["2nd_dose"]["total"] = str_to_int(dose_2)
    national_18["2nd_dose"]["new"] = str_to_int(new_dose_2)

    ###########################################################################

    # For 15-18 1st and 2nd doses.

    dose_1, dose_2 = national_table[2][3].split()
    new_dose_1, new_dose_2 = [i[1:] for i in national_table[2][4].split()
                              if i[0] == "("]

    national_15["1st_dose"]["total"] = str_to_int(dose_1)
    national_15["1st_dose"]["new"] = str_to_int(new_dose_1)

    national_15["2nd_dose"]["total"] = str_to_int(dose_2)
    national_15["2nd_dose"]["new"] = str_to_int(new_dose_2)

    ###########################################################################

    # For 12-14 1st and 2nd doses.

    dose_1, dose_2 = national_table[3][3].split()
    new_dose_1, new_dose_2 = [i[1:] for i in national_table[3][4].split()
                              if i[0] == "("]

    national_12["1st_dose"]["total"] = str_to_int(dose_1)
    national_12["1st_dose"]["new"] = str_to_int(new_dose_1)

    national_12["2nd_dose"]["total"] = str_to_int(dose_2)
    national_12["2nd_dose"]["new"] = str_to_int(new_dose_2)

    ###########################################################################

    # For 18+ 3rd dose. (18+ and 60+/HCW/FLW)

    dose_3_18, dose_3_60 = national_table[4][3].split()
    new_dose_3_18, new_dose_3_60 = [i[1:] for i in national_table[4][4].split()
                                    if i[0] == "("]

    national_18["3rd_dose"]["total"] = (str_to_int(dose_3_18)
                                        + str_to_int(dose_3_60))
    national_18["3rd_dose"]["new"] = (str_to_int(new_dose_3_18)
                                      + str_to_int(new_dose_3_60))

    ###########################################################################

    # Total vaccination for all ages will be set later.

    # Set timestamp (data is of yesterday).
    pretty["timestamp"]["vaccination"] = {
        "primary_source": "mohfw",
        "date": pretty["internal"]["yesterday"].format("DD MMM YYYY"),
        "last_fetched_unix": round(pendulum.now().timestamp())
    }

    # We proceed to set state stats now.

    pretty_states_set = set(pretty.keys()) - {"All", "internal", "timestamp"}
    pretty_states_tuple = tuple(pretty_states_set)

    # First set total doses data from the PDF.

    for i in range(3, 41):
        # Done because sometimes columns can be detected merged.
        state_name = str(states_table[0][i]) + states_table[1][i]
        state_name = state_name.strip("0123456789").strip().replace("\n", "")

        if state_name not in pretty_states_set:
            state_name = find_name(state_name, pretty_states_tuple)

        state_stats_18 = pretty[state_name]["vaccination"]["18+"]
        state_stats_15 = pretty[state_name]["vaccination"]["15-18"]
        state_stats_12 = pretty[state_name]["vaccination"]["12-14"]

        state_stats_18["1st_dose"]["total"] = str_to_int(states_table[2][i])
        state_stats_18["2nd_dose"]["total"] = str_to_int(states_table[3][i])

        state_stats_15["1st_dose"]["total"] = str_to_int(states_table[4][i])
        state_stats_15["2nd_dose"]["total"] = str_to_int(states_table[5][i])

        state_stats_12["1st_dose"]["total"] = str_to_int(states_table[6][i])
        state_stats_12["2nd_dose"]["total"] = str_to_int(states_table[7][i])

        state_stats_18["3rd_dose"]["total"] = (
            str_to_int(states_table[8][i]) + str_to_int(states_table[9][i])
        )

    # Now we set new / delta increase by comparing with previous data.

    try:
        with open(pretty["internal"]["old_filename"]) as f:
            old_data = json.load(f)  # Day before yesterday's data.

    except FileNotFoundError:
        # We don't have previous data, so can't figure out new doses.
        pass

    else:
        for old_state in (set(old_data.keys()) - {"All", "timestamp"}):
            # Do for states only as we already have delta data for national.

            if old_state in pretty_states_set:
                new_state = old_state
            else:
                new_state = find_name(old_state, pretty_states_tuple)

            old_18 = old_data[old_state]["vaccination"]["18+"]
            old_15 = old_data[old_state]["vaccination"]["15-18"]
            old_12 = old_data[old_state]["vaccination"]["15-18"]

            new_18 = pretty[new_state]["vaccination"]["18+"]
            new_15 = pretty[new_state]["vaccination"]["15-18"]
            new_12 = pretty[new_state]["vaccination"]["15-18"]

            for new, old in (
                (new_18, old_18), (new_15, old_15), (new_12, old_12)
            ):
                new["1st_dose"]["new"] = (new["1st_dose"]["total"]
                                          - old["1st_dose"]["total"])

                new["2nd_dose"]["new"] = (new["2nd_dose"]["total"]
                                          - old["2nd_dose"]["total"])

                new["3rd_dose"]["new"] = (new["3rd_dose"]["total"]
                                          - old["3rd_dose"]["total"])

    # Now set all_doses, as well as all_ages data.
    for state in (pretty_states_set | {"All"}):
        set_all_doses(pretty[state]["vaccination"]["18+"])
        set_all_doses(pretty[state]["vaccination"]["15-18"])
        set_all_doses(pretty[state]["vaccination"]["12-14"])

        set_all_ages(pretty[state]["vaccination"])
    # End of for loop.
# End of fill_mohfw_data()


# End of file.
