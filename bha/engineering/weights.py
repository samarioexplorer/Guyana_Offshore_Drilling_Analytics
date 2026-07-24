"""
==========================================================
Weights Module

Weight and center of gravity calculations.

Engineering Suite v3.0
==========================================================
"""

from __future__ import annotations

from .geometry import GeometryModule
from ..enums import ComponentType

class WeightsModule(GeometryModule):
    """
    Weight-related engineering calculations.
    """

    @property
    def total_weight(self):

        return self._cached(

            "total_weight",

            lambda: sum(

                component.weight_lb

                for component in self.bha.components

            )

        )
    
    @property
    def collar_weight(self):

        return self._cached(

            "collar_weight",

            lambda: sum(

                component.weight_lb

                for component in self.bha.components

                if component.component_type
                == ComponentType.DRILL_COLLAR

            )

        )
    
    @property
    def hwdp_weight(self):

        return self._cached(

            "hwdp_weight",

            lambda: sum(

                component.weight_lb

                for component in self.bha.components

                if component.component_type
                == ComponentType.HWDP

            )

        )
    
    @property
    def drillpipe_weight(self):

        return self._cached(

            "drillpipe_weight",

            lambda: sum(

                component.weight_lb

                for component in self.bha.components

                if component.component_type
                == ComponentType.DRILL_PIPE

            )

        )
    
    @property
    def bit_weight(self):

        if self.bha.bit is None:

            return 0.0

        return self.bha.bit.weight_lb
    
    @property
    def motor_weight(self):

        if self.bha.motor is None:

            return 0.0

        return self.bha.motor.weight_lb
    
    @property
    def rss_weight(self):

        if self.bha.rss is None:

            return 0.0

        return self.bha.rss.weight_lb
    
    @property
    def mwd_weight(self):

        if self.bha.mwd is None:

            return 0.0

        return self.bha.mwd.weight_lb
    
    @property
    def average_weight_per_ft(self):

        if self.total_length == 0:
            return 0.0

        return self.total_weight / self.total_length