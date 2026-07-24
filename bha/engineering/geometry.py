"""
==========================================================
Geometry Module

Geometry calculations.

Engineering Suite v3.0
==========================================================
"""

from __future__ import annotations

from .base import EngineeringBase


class GeometryModule(EngineeringBase):

    @property
    def component_count(self):

        return len(self.bha.components)

    # -----------------------------------------------------

    @property
    def total_length(self):

        return self._cached(

            "total_length",

            lambda: sum(

                component.length_ft

                for component in self.bha.components

            )

        )

    # -----------------------------------------------------

    @property
    def average_od(self):

        if not self.bha.components:

            return 0.0

        return sum(

            component.outer_diameter_in

            for component in self.bha.components

        ) / len(self.bha.components)

    @property
    def average_outer_diameter(self):
        return self.average_od
 
    # -----------------------------------------------------
    @property
    def average_id(self):

        if not self.bha.components:

            return 0.0

        return sum(

            component.inner_diameter_in

            for component in self.bha.components

        ) / len(self.bha.components)
    
    @property
    def average_inner_diameter(self):
        return self.average_id