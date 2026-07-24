"""
==========================================================
Buckling Module

Engineering Suite v3.0

Drill string buckling calculations.
==========================================================
"""

from __future__ import annotations

from math import sqrt

from .hydraulics import HydraulicsModule

from ..constants import (
    STEEL_YOUNGS_MODULUS_PSI,
    LOW_BUCKLING_RATIO,
    MODERATE_BUCKLING_RATIO,
)

class BucklingModule(HydraulicsModule):
    """
    Drill string buckling calculations.
    """

    @property
    def neutral_point(self):
        collars = [
            c for c in self.bha.components
            if c.component_type.name == "DRILL_COLLAR"
        ]

        if not collars:
            return 0.0

        collar_length = sum(c.length_ft for c in collars)

        if self.collar_weight == 0:
            return 0.0

        return (self.recommended_wob / self.collar_weight) * collar_length

    @property
    def collar_length(self):
        return sum(
            c.length_ft
            for c in self.bha.components
            if c.component_type.name == "DRILL_COLLAR"
        )

    @property
    def buckling_ratio(self):
        if self.available_wob == 0:
            return 0.0

        return self.recommended_wob / self.available_wob

    @property
    def critical_buckling_load(self):
        if self.average_outer_diameter == 0:
            return 0.0

        inertia = (3.14159 * self.average_outer_diameter**4) / 64

        if self.total_length == 0:
            return 0.0

        return (
            (3.14159**2)
            * STEEL_YOUNGS_MODULUS_PSI
            * inertia
            / (self.total_length**2)
        )

    @property
    def buckling_safety_factor(self):
        if self.recommended_wob == 0:
            return 0.0

        return self.critical_buckling_load / self.recommended_wob

    @property
    def buckling_status(self):
        ratio = self.buckling_ratio

        if ratio < LOW_BUCKLING_RATIO:
            return "Low"

        if ratio < MODERATE_BUCKLING_RATIO:
            return "Moderate"

        return "High"

    @property
    def buckling_recommendation(self):
        if self.buckling_status == "Low":
            return "Safe operating range."

        if self.buckling_status == "Moderate":
            return "Monitor WOB and collar length."

        return "Reduce WOB or increase drill collar section."
    
    