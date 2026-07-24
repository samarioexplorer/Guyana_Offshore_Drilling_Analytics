"""
==========================================================
Engineering Base Class

Shared cache and utilities.

Engineering Suite v3.0
==========================================================
"""

from __future__ import annotations


class EngineeringBase:
    """
    Base class for all engineering modules.
    """

    def __init__(self, bha):

        self.bha = bha

        self._cache = {}

    # -----------------------------------------------------

    def clear_cache(self):

        self._cache.clear()

    # -----------------------------------------------------

    def _cached(self, key, calculation):

        if key not in self._cache:

            self._cache[key] = calculation()

        return self._cache[key]