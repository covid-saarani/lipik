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

# Import the main filling functions.
from .mohfw import fill_mohfw_data
from .mygov import fill_mygov_data
from .mygov_centers import fill_state_centers


def fill_vaccination(pretty: dict[str, Any]) -> None:
    """
    Fetches data from either MyGov or MoHFW, and fills in the `pretty` dict.

    If pretty["internal"]["use_mygov"] is True, then MyGov JSON is parsed.
    Otherwise, PDF from MoHFW website is parsed.

    This is done to avoid mismatch in data streams, and because PDF detection
    (even though is very accurate) can be wonky due to inherent randomness or
    changes in the table layout.

    Regardless, number of centers in the states is fetched from MyGov.
    """
    fill_state_centers(pretty)

    if pretty["internal"]["use_mygov"]:
        fill_mygov_data(pretty)
    else:
        fill_mohfw_data(pretty)
# End of fill_vaccination()


# End of file.
