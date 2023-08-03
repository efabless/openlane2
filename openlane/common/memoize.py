# Copyright 2023 Efabless Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from functools import lru_cache, wraps


def memoize(cache_size: int = 16):
    """
    Creates a decorator that `memoizes <https://en.wikipedia.org/wiki/Memoization>`_
    the results for a number of calls to a function. Useful for expensive pure
    functions.

    :param cache_size: The number of entries in the memoization cache.
    :returns: The decorator
    """

    @wraps
    def decorator(f):
        return lru_cache(cache_size, True)(f)

    return decorator
