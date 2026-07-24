"""
==========================================================
Hydraulics Module

Engineering Suite v3.0

Hydraulic calculations for drilling operations.
==========================================================
"""

from __future__ import annotations

from math import pi

from .wob import WOBModule

from ..constants import (
    HYDRAULIC_HP_CONSTANT,
    JET_VELOCITY_CONSTANT,
)

class HydraulicsModule(WOBModule):
    """
    Hydraulic engineering calculations.
    """

    @property
    def hydraulic_horsepower(self):

        return self._cached(

            "hydraulic_horsepower",

            lambda:

            (

                self.bha.flow_rate_gpm

                *

                self.bha.pump_pressure_psi

            )

            /

            HYDRAULIC_HP_CONSTANT

        )
    
    @property
    def bit_hydraulic_horsepower(self):

        return self._cached(

            "bit_hydraulic_horsepower",

            lambda:

            (

                self.bha.flow_rate_gpm

                *

                self.bha.bit_pressure_loss_psi

            )

            /

            HYDRAULIC_HP_CONSTANT

        )
    
    @property
    def bit_hydraulic_horsepower(self):

        return self._cached(

            "bit_hydraulic_horsepower",

            lambda:

            (

                self.bha.flow_rate_gpm

                *

                self.bha.bit_pressure_loss_psi

            )

            /

            HYDRAULIC_HP_CONSTANT

        )
    
    @property
    def hydraulic_efficiency(self):

        if self.hydraulic_horsepower == 0:

            return 0.0

        return (

            self.bit_hydraulic_horsepower

            /

            self.hydraulic_horsepower

        )
    
    @property
    def jet_velocity(self):

        if self.bha.nozzle_area_in2 == 0:

            return 0.0

        return (

            JET_VELOCITY_CONSTANT

            *

            self.bha.flow_rate_gpm

            /

            self.bha.nozzle_area_in2

        )

    @property
    def hydraulic_horsepower_per_square_inch(self):

        if self.bha.bit is None:

            return 0.0

        bit_area = (

            pi

            *

            self.bha.bit.outer_diameter_in ** 2

        ) / 4

        if bit_area == 0:

            return 0.0

        return (

            self.bit_hydraulic_horsepower

            /

            bit_area

        )

    @property
    def bit_cleaning_index(self):

        if self.jet_velocity == 0:

            return 0.0

        return (

            self.jet_velocity

            *

            self.hydraulic_efficiency

        )

    @property
    def hydraulic_status(self):

        if self.bit_cleaning_index < 80:

            return "Poor"

        if self.bit_cleaning_index < 120:

            return "Fair"

        if self.bit_cleaning_index < 180:

            return "Good"

        return "Excellent"

