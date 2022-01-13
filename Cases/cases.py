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

# Import the main filling functions.
from .mohfw import parse_mohfw
from .mygov import parse_mygov


def fill_cases(
    pretty: dict[str, Any],
    yesterday: pendulum.DateTime
) -> None:
    """
    Fetches data from MyGov and MoHFW, and fills in the `pretty` dict.

    If MyGov data is outdated, the internal bool is set to False, and MoHFW
    data is used.
    """
    mohfw = requests.get(pretty["internal"]["mohfw_cases"]).json()
    mygov = requests.get(pretty["internal"]["mygov_cases"]).json()

    # 0th is A&N Islands. Check total cases, it cannot decrease with time.
    if mygov["Total Confirmed cases"]["0"] < mohfw[0]["new_positive"]:
        # MyGov data is outdated compared to the MoHFW one.
        pretty["internal"]["use_mygov"] = False
        parse_mygov(pretty, mygov, yesterday, fill_data=False)
        parse_mohfw(pretty, mohfw, yesterday)
        return

    # else:
    # Parse MyGov data, and add reconciled death data from MoHFW data.
    parse_mygov(pretty, mygov, yesterday)
    parse_mohfw(pretty, mohfw, yesterday, reconciliation_only=True)
# End of fill_cases().


# End of file.
