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
from string import digits
from tempfile import NamedTemporaryFile
from typing import Any

# Import external dependencies.
import camelot
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


def set_all_ages_doses(vaccination_dict: dict[str, Any]) -> None:
    """
    1. Set all_doses dict for each age group by adding up the dose stats.
    2. Set doses for all ages by adding up 18+ and 15-18 numbers.
    """

    doses_18 = vaccination_dict["18+"]
    doses_15 = vaccination_dict["15-18"]
    doses_all = vaccination_dict["all_ages"]

    # Set agewise all_dose numbers.

    doses_18["all_doses"]["total"] = (doses_18["1st_dose"]["total"]
                                      + doses_18["2nd_dose"]["total"]
                                      + doses_18["3rd_dose"]["total"])

    doses_18["all_doses"]["new"] = (doses_18["1st_dose"]["new"]
                                    + doses_18["2nd_dose"]["new"]
                                    + doses_18["3rd_dose"]["new"])

    doses_15["all_doses"]["total"] = (doses_15["1st_dose"]["total"]
                                      + doses_15["2nd_dose"]["total"]
                                      + doses_15["3rd_dose"]["total"])

    doses_15["all_doses"]["new"] = (doses_15["1st_dose"]["new"]
                                    + doses_15["2nd_dose"]["new"]
                                    + doses_15["3rd_dose"]["new"])

    # Set cumulative numbers.

    doses_all["all_doses"]["total"] = (doses_18["all_doses"]["total"]
                                       + doses_15["all_doses"]["total"])

    doses_all["all_doses"]["new"] = (doses_18["all_doses"]["new"]
                                     + doses_15["all_doses"]["new"])

    doses_all["1st_dose"]["total"] = (doses_18["1st_dose"]["total"]
                                      + doses_15["1st_dose"]["total"])

    doses_all["1st_dose"]["new"] = (doses_18["1st_dose"]["new"]
                                    + doses_15["1st_dose"]["new"])

    doses_all["2nd_dose"]["total"] = (doses_18["2nd_dose"]["total"]
                                      + doses_15["2nd_dose"]["total"])

    doses_all["2nd_dose"]["new"] = (doses_18["2nd_dose"]["new"]
                                    + doses_15["2nd_dose"]["new"])

    doses_all["3rd_dose"]["total"] = (doses_18["3rd_dose"]["total"]
                                      + doses_15["3rd_dose"]["total"])

    doses_all["3rd_dose"]["new"] = (doses_18["3rd_dose"]["new"]
                                    + doses_15["3rd_dose"]["new"])
# End of set_all_ages_doses()


def fill_mohfw_data(
    pretty: dict[str, Any],
    yesterday: pendulum.DateTime,
    day_before_yesterday: pendulum.DateTime
) -> None:
    """Get state vaccination stats from MoHFW PDF, and fill it in `pretty`."""

    pdf = NamedTemporaryFile(suffix=".pdf")
    pdf.write(requests.get(pretty["internal"]["mohfw_vaccination"]).content)

    # Parse the table from the pdf. Linux needed for using an open file.
    tables = camelot.read_pdf(pdf.name)
    pdf.close()  # We no longer need it. Also will delete the same.

    # Make sure we have tables parsed in the expected format.
    # See the example CSV file for the expected format.

    if len(tables) != 2:
        raise InvalidPdfException("There must be 2 tables.")

    if tables[0].accuracy < 95 or tables[1].accuracy < 90:
        raise InvalidPdfException("Cannot detect the tables accurately.")

    national_table = tables[0].df
    states_table = tables[1].df

    if (
        len(national_table) != 5
        or len(national_table.columns) != 5

        or national_table[1][2].count("\n") != 1  # 1st dose\n2nd dose.
        or national_table[1][3].count("\n") != 1  # Numbers of doses.
        or national_table[1][4].count("\n") != 3  # Last 24 hours stat.

        or national_table[2][2].count("\n") != 0  # 15-18's 1st dose.
        or national_table[2][3].count("\n") != 0  # Number of ^.
        or national_table[2][4].count("\n") != 1  # Last 24 hours stat.

        or national_table[3][2]  # If Empty string. | Precaution dose.
        or national_table[3][3].count("\n") != 0  # Number of ^.
        or national_table[3][4].count("\n") != 1  # Last 24 hours stat.
    ):
        raise InvalidPdfException("National vaccination stats "
                                  "not parsed correctly.")

    if len(states_table) != 41 or len(states_table.columns) != 7:
        raise InvalidPdfException("State-wise vaccination stats "
                                  "not parsed correctly.")

    # Set timestamp (= as on 7 AM of today, data is of yesterday).
    pretty["timestamp"]["vaccination"] = {
        "date": yesterday.format("DD MMM YYYY"),
        "as_on": pendulum.today("Asia/Kolkata").format("DD MMM YYYY 07:00 zz"),
        "last_fetched_unix": round(pendulum.now().timestamp())
    }

    # Now, set national stats.

    national_18 = pretty["All"]["vaccination"]["18+"]
    national_15 = pretty["All"]["vaccination"]["15-18"]

    # For 18+ first and second doses:

    total = national_table[1][3].split("\n")
    new = national_table[1][4].split("\n")

    national_18["1st_dose"]["total"] = locale.atoi(total[0])
    national_18["1st_dose"]["new"] = locale.atoi(new[0].split()[0][1:])

    national_18["2nd_dose"]["total"] = locale.atoi(total[1])
    national_18["2nd_dose"]["new"] = locale.atoi(new[1].split()[0][1:])

    # For 18+ precaution dose:
    national_18["3rd_dose"]["total"] = locale.atoi(national_table[3][3])
    national_18["3rd_dose"]["new"] = locale.atoi(
                                        national_table[3][4].split()[0][1:])

    # For 15-18 1st dose:
    national_15["1st_dose"]["total"] = locale.atoi(national_table[2][3])
    national_15["1st_dose"]["new"] = locale.atoi(
                                        national_table[2][4].split()[0][1:])

    # Total vaccination for all ages will be set later.

    # We proceed to set state stats now.

    pretty_states_set = set(pretty.keys()) - {"All", "internal", "timestamp"}
    pretty_states_tuple = tuple(pretty_states_set)

    # First set total doses data from the PDF.

    for i in range(3, 41):
        # Done because sometimes columns can be detected merged.
        state_name = str(states_table[0][i]) + states_table[1][i]
        state_name = state_name.strip(digits)

        if state_name not in pretty_states_set:
            state_name = find_name(state_name, pretty_states_tuple)

        state_stats_18 = pretty[state_name]["vaccination"]["18+"]
        state_stats_15 = pretty[state_name]["vaccination"]["15-18"]

        state_stats_18["1st_dose"]["total"] = locale.atoi(states_table[2][i])
        state_stats_18["2nd_dose"]["total"] = locale.atoi(states_table[3][i])
        state_stats_18["3rd_dose"]["total"] = locale.atoi(states_table[5][i])

        # For 15+, 1st dose only, so 1st dose == all doses.
        state_stats_15["1st_dose"]["total"] = locale.atoi(states_table[4][i])

    # Now we set new / delta increase by comparing with previous data.

    old_filename = ("../saarani/" + day_before_yesterday.format("YYYY_MM_DD")
                    + ".json")

    try:
        with open(old_filename) as f:
            old_data = json.load(f)
    except FileNotFoundError:
        # We don't have previous data, so can't figure out new doses.
        pass
    else:
        old_as_on = old_data["timestamp"]["vaccination"]["as_on"]

        # Do for states only, and only if we have the previous day's data.
        if old_as_on.split()[0] == yesterday.format("DD MMM YYYY"):
            for old_state in (set(old_data.keys()) - {"All", "timestamp"}):
                if old_state in pretty_states_set:
                    new_state = old_state
                else:
                    new_state = find_name(state_name, pretty_states_tuple)

                old_18 = old_data[old_state]["vaccination"]["18+"]
                old_15 = old_data[old_state]["vaccination"]["15-18"]
                new_18 = pretty[new_state]["vaccination"]["18+"]
                new_15 = pretty[new_state]["vaccination"]["15-18"]

                new_18["1st_dose"]["new"] = (new_18["1st_dose"]["total"]
                                             - old_18["1st_dose"]["total"])

                new_18["2nd_dose"]["new"] = (new_18["2nd_dose"]["total"]
                                             - old_18["2nd_dose"]["total"])

                new_18["3rd_dose"]["new"] = (new_18["3rd_dose"]["total"]
                                             - old_18["3rd_dose"]["total"])

                new_15["1st_dose"]["new"] = (new_15["1st_dose"]["total"]
                                             - old_15["1st_dose"]["total"])

                new_15["2nd_dose"]["new"] = (new_15["2nd_dose"]["total"]
                                             - old_15["2nd_dose"]["total"])

                new_15["3rd_dose"]["new"] = (new_15["3rd_dose"]["total"]
                                             - old_15["3rd_dose"]["total"])

    # Now set all_doses, as well as all_ages data.
    for state in pretty_states_set:
        set_all_ages_doses(pretty[state]["vaccination"])
# End of fill_mohfw_data()


# End of file.
