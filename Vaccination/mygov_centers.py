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
import requests

# Import helper function.
from Helpers.fuzzy_find_name import find_name


def fill_state_centers(pretty: dict[str, Any]) -> None:
    """Fetches number of centers in states, and puts them in `pretty`."""
    centers = requests.get(pretty["internal"]["mygov_state_centers"]).json()

    pretty_states_set = set(pretty.keys()) - {"All", "internal", "timestamp"}
    pretty_states_tuple = tuple(pretty_states_set)

    for i in centers:
        if i["state_name"] in pretty_states_set:
            state_name = i["state_name"]
        else:
            state_name = find_name(i["state_name"], pretty_states_tuple)

        pretty[state_name]["vaccination"]["centers"] += i["centers"]
        pretty["All"]["vaccination"]["centers"] += i["centers"]  # Nationally.
# End of fill_state_centers()


# End of file.
