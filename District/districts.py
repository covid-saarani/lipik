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
import pickle
from tempfile import NamedTemporaryFile
from typing import Any

# Import external dependencies.
import pendulum
import pylightxl
import requests

# Import helper functions.
from Helpers.fuzzy_find_name import find_name
from .district_helper import district_name_fixer


def fill_district_data(pretty: dict[str, Any]) -> None:
    """Get the district data / numbers, and fill them in the `pretty` dict."""

    # We have saved names of almost all districts with their respective states.
    # Hence, we will first create their dicts in the data and then fill them.
    # Note that districts of DL, LD aren't there, so create them later.

    with open("./District/districts.pickle", "rb") as f:
        state_district_map = pickle.load(f)

    pretty_states_set = set(pretty.keys()) - {"All", "internal", "timestamp"}
    pretty_states_tuple = tuple(pretty_states_set)
    state_district_map_keys = set(state_district_map.keys())

    district_struct = {
        "centers": 0,
        "rat_pc": 0,
        "rtpcr_pc": 0,
        "positivity_rate": 0,
        "iteration": 0  # To delete later
    }

    for state in pretty_states_set:
        if (abbr := pretty[state]["abbr"]) in state_district_map_keys:
            for district in state_district_map[abbr]:
                if district in ("Unknown", "Other State"):
                    continue
                # else:
                pretty[state]["districts"][district] = copy.deepcopy(
                                                            district_struct)

    # Get number of centers in districts from JSON, and save them.

    centers = requests.get(pretty["internal"]["mygov_district_centers"]).json()

    for data in centers:
        if data["state_name"] in pretty_states_set:
            state = data["state_name"]
        else:
            state = find_name(data["state_name"], pretty_states_tuple)

        state_districts_dict = pretty[state]["districts"]
        state_district_names = state_district_map[pretty[state]["abbr"]]

        district = district_name_fixer(data["district_name"], state)

        if state in ("Delhi", "Lakshadweep"):
            state_districts_dict[district] = copy.deepcopy(district_struct)
            state_district_map[pretty[state]["abbr"]].append(district)

        elif district not in set(state_district_names):
            district = find_name(district, tuple(state_district_names))

        # Now set the number of centres.
        state_districts_dict[district]["centers"] += data["centers"]

    # Now we will parse the excel file.

    # The URL can be at times invalid, and changing date may work.
    xlsx_url = pretty["internal"]["mohfw_xlsx"]
    xlsx_date_str = xlsx_url.split(".")[-2][-9:]  # Example: 13Jan2022
    xlsx_date = pendulum.from_format(xlsx_date_str, "DDMMMYYYY")

    for i in range(3):  # Will check 3 times -> Current, -1 day, -2 days.
        response = requests.get(xlsx_url)
        if response.status_code == 200:
            break
        else:
            new_date = xlsx_date.subtract(days=(i + 1)).format("DDMMMYYYY")
            xlsx_url = xlsx_url.replace(xlsx_date_str, new_date)
    else:
        # For loop didn't break.
        raise ValueError("Cannot get district xlsx file (status_code != 200).")

    file = NamedTemporaryFile(suffix=".xlsx")
    file.write(response.content)

    xlsx = pylightxl.readxl(file.name)
    sheet = xlsx.ws("Sheet1")

    file.close()

    # Set timestamps and meta data.

    pretty["timestamp"]["districts"] = {
        "week": sheet.address("B7"),
        "last_fetched_unix": round(pendulum.now().timestamp())
    }

    # There will be 3 tables, with 5 columns (+ 1 for serial number).
    # Columns: Table 1 - C to G  ;  Table 2 - J to N  ;  Table 3 - Q to U
    # Their entries (excluding heading) will start at 12th row.
    # We will continue to parse next row until we reach the "Grand Total" row.
    # After end of parsing one table, we will move to another.

    table_cols = (("C", "G"), ("J", "N"), ("Q", "U"))

    for i in range(3):
        j = 12
        col1, col2 = table_cols[i]
        state = ""  # Save it, as merged cells have the entry only in 1st cell.

        while True:
            data = sheet.range(address=f"{col1}{j}:{col2}{j}")[0]

            if data[0] == "Grand Total":
                break

            if data[0]:  # If not empty string.
                state = data[0].title().replace("And", "and")
                if state not in pretty_states_set:
                    state = find_name(state, pretty_states_tuple)

            state_districts_dict = pretty[state]["districts"]
            district_names_set = set(pretty[state]["districts"].keys())
            district_names_tuple = tuple(district_names_set)

            district = district_name_fixer(data[1].title(), state)

            if district not in district_names_set:
                if (new_dist := f"{district} {state}") in district_names_set:
                    district = new_dist
                else:
                    try:
                        district = find_name(district, district_names_tuple)
                    except ValueError:
                        print(state, district, "\n", state_district_names)
                        state_districts_dict[district] = copy.deepcopy(
                                                            district_struct)

            state_districts_dict[district]["rat_pc"] += data[2]
            state_districts_dict[district]["rtpcr_pc"] += data[3]
            state_districts_dict[district]["positivity_rate"] += data[4]
            state_districts_dict[district]["iteration"] += 1

            j += 1
        # End of while loop.
    # End of for loop.

    # If we added multiple times, we need to average out the percentages.
    for state in pretty_states_set:
        for district in (districts := pretty[state]["districts"]):
            dist_dict = districts[district]

            # Divide if > 1 (already summed up).
            if (num := districts[district]["iteration"]) > 1:
                dist_dict["rat_pc"] = round((dist_dict["rat_pc"] / num), 5)
                dist_dict["rtpcr_pc"] = round((dist_dict["rtpcr_pc"] / num), 5)
                dist_dict["positivity_rate"] = round(
                    (dist_dict["positivity_rate"] / num), 5
                )

            # Delete the field.
            del dist_dict["iteration"]

    # Now we will set aggregate national stats.

    natl = copy.deepcopy(district_struct)

    for state in pretty_states_set:
        for district in (districts := pretty[state]["districts"]):
            natl["centers"] += districts[district]["centers"]
            natl["rat_pc"] += districts[district]["rat_pc"]
            natl["rtpcr_pc"] += districts[district]["rtpcr_pc"]
            natl["positivity_rate"] += districts[district]["positivity_rate"]
            natl["iteration"] += 1

    num = natl["iteration"]
    del natl["iteration"]

    natl["rat_pc"] = round((natl["rat_pc"] / num), 5)
    natl["rtpcr_pc"] = round((natl["rtpcr_pc"] / num), 5)
    natl["positivity_rate"] = round((natl["positivity_rate"] / num), 5)

    pretty["All"]["districts"]["Aggregate"] = natl
# End of fill_district_data()


# End of file.
