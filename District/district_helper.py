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


def district_name_fixer(district, state) -> str:
    """Fix / Change district names."""

    change_names = {  # For typos/old/long/short -> new name map.
        "Kawardha": "Kabeerdham",
        "BBMP": "Bengaluru Urban",
        "Sri Potti Sriramulu Nellore": "S.P.S. Nellore",
        "Gulbarga": "Kalaburagi",
        "Aranthangi": "Pudukkottai",
        "Attur": "Salem",
        "Cheyyar": "Tiruvannamalai",
        "Kovilpatti": "Thoothukkudi",
        "Palani": "Dindigul",
        "Paramakudi": "Ramanathapuram",
        "Poonamallee": "Thiruvallur",
        "Sivakasi": "Virudhunagar",
        "Tuticorin": "Thoothukkudi",
        "Dibang Valley": "Upper Dibang Valley",
        "Kamrup Metro": "Kamrup Metropolitan",
        "Baleshwar": "Balasore",
        "East Nimar": "Khandwa",
        "Sonepur": "Subarnapur",
        "Korea": "Koriya",
        "Diamond Harbor HD (S 24 Parganas)": "South 24 Parganas",
        "Nandigram HD (Purba Medinipore)": "Purba Medinipur",
        "Shahid Bhagat Singh Nagar": "SBS Nagar",
        "Dohad": "Dahod",
        "Agar": "Agar Malwa",
    }

    if district in change_names:
        return change_names[district]

    # Typically in Gujarat, Urban Municipal centers are listed separately.
    if district.endswith("Corporation"):
        district = district.replace(" Corporation", "")

    if state == "West Bengal":
        district = district.replace("East", "Purba")
        district = district.replace("West", "Paschim")
    else:
        district = district.replace("Purba", "East")
        district = district.replace("Purbi", "East")
        district = district.replace("Paschim", "West")
        district = district.replace("Pashchim", "West")

    return district
# End of district_name_fixer()


# End of file.
