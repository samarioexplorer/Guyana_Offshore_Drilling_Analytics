"""
==========================================================
Weight On Bit (WOB) Module

Engineering Suite v3.0

Professional drilling engineering calculations.
==========================================================
"""

from __future__ import annotations

from .weights import WeightsModule
from ..constants import (
    COLLAR_WOB_FACTOR,
    WOB_STATUS_LIMIT_LOW,
    WOB_STATUS_LIMIT_HIGH,
)

class WOBModule(WeightsModule):
    """
    Weight On Bit calculations.
    """

    @property
    def available_wob(self):

        return self._cached(

            "available_wob",

            lambda:

                self.collar_weight
                * COLLAR_WOB_FACTOR

        )
    
    @property
    def recommended_wob(self):

        bit = self.bha.bit

        if bit is None:

            return 0.0

        diameter = bit.outer_diameter_in

        if diameter >= 17.0:
            return 60000

        if diameter >= 12.25:
            return 45000

        if diameter >= 8.5:
            return 30000

        return 20000
    
    @property
    def wob_utilization(self):

        if self.available_wob == 0:

            return 0.0

        return (

            self.recommended_wob

            /

            self.available_wob

        )
    
    @property
    def wob_reserve(self):

        if self.available_wob == 0:

            return 0.0

        return (

            self.available_wob

            -

            self.recommended_wob

        )
    
    @property
    def wob_reserve_percent(self):

        if self.available_wob == 0:

            return 0.0

        return (

            self.wob_reserve

            /

            self.available_wob

            * 100

        )
    
    @property
    def neutral_point(self):

        collars = [

            c

            for c in self.bha.components

            if c.component_type == ComponentType.DRILL_COLLAR

        ]

        if not collars:

            return 0.0

        collar_length = sum(

            c.length_ft

            for c in collars

        )

        if self.collar_weight == 0:

            return 0.0

        return (

            self.recommended_wob

            /

            self.collar_weight

        ) * collar_length
    
    @property
    def wob_status(self):

        ratio = self.wob_utilization

        if ratio < WOB_STATUS_LIMIT_LOW:

            return "Underloaded"

        if ratio < WOB_STATUS_LIMIT_HIGH:

            return "Optimal"

        return "Overloaded"
    
    @property
    def wob_safety_factor(self):

        if self.recommended_wob == 0:

            return 0.0

        return (

            self.available_wob

            /

            self.recommended_wob

        )
    
    @property
    def wob_safety_factor(self):

        if self.recommended_wob == 0:

            return 0.0

        return (

            self.available_wob

            /

            self.recommended_wob

        )