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
from functools import lru_cache

# Import external dependencies.
from thefuzz import process as thefuzz_process


@lru_cache(maxsize=None)
def find_name(name: str, name_set: tuple[str]) -> str:
    """
    Given a name, find the state/district having the closest spelling.

    Using fuzzy matching, as there can be typos, or some names can be split or
    written in different ways. Examples are:
        - "A & N Islands" for "Andaman and Nicobar Islands",
        - "Telengana" instead of "Telangana",
        - Separate "Daman & Diu" and "Dadra & Nagar Haveli" instead of merged.
    """

    entry = thefuzz_process.extractOne(name, name_set, score_cutoff=50,
                                       processor=lambda x: x)

    if entry is not None:
        return entry[0]

    # else: Account for different spellings for आ, ई, ऊ.
    vowels = {"aa": "a", "ee": "i", "oo": "u", "y": "i"}

    for vowel in vowels.keys():
        if vowel in name:
            return find_name(name.replace(vowel, vowels[vowel]), name_set)
    else:
        raise ValueError(f"Cannot find entry for '{name}'.")
# End of find_name()


# End of file.
