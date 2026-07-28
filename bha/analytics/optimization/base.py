"""
==========================================================
Optimization Base Class

Engineering Suite v4.2

Common functionality for optimization engines

==========================================================
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class OptimizationBase:
    """
    Base class for optimization modules.
    """

    def validate(self):
        """
        Override in child classes.
        """
        pass