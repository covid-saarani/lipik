###############################################################################

# Covid Saarani is a COVID-19 data API.
# Lipik fetches the related data from official Indian government sources.

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
import json
from pathlib import Path

# Import external dependencies.
from bs4 import BeautifulSoup
import pendulum
import requests

# Import the populator functions.
from Cases.cases import fill_cases
from District.districts import fill_district_data
from Vaccination.vaccination import fill_vaccination


pretty = {}  # Formatted dict containing all data for a state.
pretty["timestamp"] = {}  # For storing timestamps of data.

# For internal use, will delete later.
mygov_url = "https://www.mygov.in/sites/default/files/covid/"
pretty["internal"] = {
    "use_mygov": True,
    "mygov_cases": mygov_url + "covid_state_counts_ver1.json",
    "mygov_vaccination": mygov_url + "vaccine/vaccine_counts_today.json",
    "mygov_state_centers": mygov_url + "vaccine/vaccination_states.json",
    "mygov_district_centers": mygov_url + "vaccine/vaccination_districts.json",
    "mohfw_cases": "https://www.mohfw.gov.in/data/datanew.json"
}

# Parse MoHFW website and get the requisite links.
soup = BeautifulSoup(requests.get("https://www.mohfw.gov.in").text, "lxml")
for link_tag in soup.findAll("a"):

    if "District-wise COVID-19 test positivity rates" in str(link_tag):
        pretty["internal"]["mohfw_xlsx"] = link_tag.get("href")

    elif "Vaccination State Data" in str(link_tag):
        pretty["internal"]["mohfw_vaccination"] = link_tag.get("href")


# Make a dict for national data (Same structure used for state data).
# National stats will be filled later as we populate state stats.

pretty["All"] = {
    # Collapse / Fold this for skipping / better readability of later code.
    # Check the parsing functions to understand better as we populate the dict.

    "abbr": "IN",  # State code (2 letter abbreviation).
    "hindi": "भारत",  # Name of state in Hindi. Useful for l10n.
    "helpline": "1075, 011-23978046",  # State helpline for COVID.
    "donate": "https://www.pmcares.gov.in/",   # For donating to state funds.

    "confirmed": {
        "current": 0,     # As on the previous day of logging (say, 100).
        "previous": 0,    # As on the day before yesterday day (say, 70).
        "new": 0,       # New cases (for the examples above, 30).
    },

    "active": {
        "current": 0,
        "previous": 0,
        "new": 0,
        "ratio_pc": 0
    },

    "recovered": {
        "current": 0,
        "previous": 0,
        "new": 0,
        "ratio_pc": 0
    },

    "deaths": {
        "current": 0,
        "previous": 0,
        "new": 0,
        "reconciled": 0,
        "ratio_pc": 0
    },

    "vaccination": {
        "centers": 0,  # Number of vaccination centers.

        "all_ages": {  # Self explanatory fields. "new" => Last 24 hours.
            "all_doses": {"total": 0, "new": 0},
            "1st_dose": {"total": 0, "new": 0},
            "2nd_dose": {"total": 0, "new": 0},
            "3rd_dose": {"total": 0, "new": 0},
        },

        "18+": {
            "all_doses": {"total": 0, "new": 0},
            "1st_dose": {"total": 0, "new": 0},
            "2nd_dose": {"total": 0, "new": 0},
            "3rd_dose": {"total": 0, "new": 0},
        },

        "15-18": {
            "all_doses": {"total": 0, "new": 0},
            "1st_dose": {"total": 0, "new": 0},
            "2nd_dose": {"total": 0, "new": 0},
            "3rd_dose": {"total": 0, "new": 0},
        },
    },

    "districts": {}
}

# For data not linked to any state.
pretty["Miscellaneous"] = copy.deepcopy(pretty["All"])  # Copying defaults.
pretty["Miscellaneous"]["abbr"] = "misc"
pretty["Miscellaneous"]["hindi"] = "इत्यादि"
pretty["Miscellaneous"]["helpline"] = ""
pretty["Miscellaneous"]["donate"] = ""


# Yesterday and day before yesterday.
yesterday = pendulum.yesterday("Asia/Kolkata")
day_before_yesterday = yesterday.subtract(days=1)

# Fill the dictionary.
fill_cases(pretty, yesterday)
fill_vaccination(pretty, yesterday, day_before_yesterday)
fill_district_data(pretty)

# Move Miscellaneous at the end, and delete the "internal" dict.
pretty["Miscellaneous"] = pretty.pop("Miscellaneous")
del pretty["internal"]


# Save the data in JSON, and make "latest.json" symlink point to it.

Path(f"../saarani/Daily/{yesterday.format('YYYY_MM_DD')}.json").write_text(
    json.dumps(pretty, indent=4)
)

latest = Path("../saarani/latest.json")
latest.unlink(missing_ok=True)
latest.symlink_to(Path(f"./Daily/{yesterday.format('YYYY_MM_DD')}.json"))


# Make dashboard json (an unnested json).

dashboard = []

for state in pretty.keys():
    if state == "timestamp":
        continue

    vaccination_all = pretty[state]["vaccination"]["all_ages"]["all_doses"]

    dashboard.append({
        "State": "All over India" if state == "All" else state,

        "Active (Total)": pretty[state]["active"]["current"],
        "Active (New)": pretty[state]["active"]["new"],

        "Recovered (Total)": pretty[state]["recovered"]["current"],
        "Recovered (New)": pretty[state]["recovered"]["new"],

        "Deaths (Total)": pretty[state]["deaths"]["current"],
        "Deaths (New)": pretty[state]["deaths"]["new"],

        "Overall (Total)": pretty[state]["confirmed"]["current"],
        "Overall (New)": pretty[state]["confirmed"]["new"],

        "Vaccinations (Total)": vaccination_all["total"],
        "Vaccinations (New)": vaccination_all["new"],
    })

# Save dashboard in "dashboard.json".
Path("../saarani/dashboard.json").write_text(json.dumps(dashboard, indent=4))


# End of file.
