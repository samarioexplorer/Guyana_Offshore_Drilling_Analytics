"""
========================================================================
BHA Engineering Suite v2.1

engineering.py

Professional engineering calculation engine for
Bottom Hole Assemblies.

Author : Anibal Ceballos
Project : Guyana Offshore Drilling Analytics
========================================================================
"""

from __future__ import annotations

from math import pi
from statistics import mean
from typing import Callable

from .assembly import BottomHoleAssembly
from .enums import ComponentType
from . import constants


class BHAEngineering:
    """
    Engineering calculation engine.

    One instance evaluates one Bottom Hole Assembly.

    All engineering calculations are cached to avoid
    unnecessary recalculation.
    """

    ####################################################################
    # Constructor
    ####################################################################

    def __init__(
        self,
        bha: BottomHoleAssembly
    ) -> None:

        self.bha = bha

        self._cache: dict = {}

    ####################################################################
    # Cache
    ####################################################################

    def clear_cache(self) -> None:
        """
        Clears every cached engineering calculation.
        """

        self._cache.clear()

    ####################################################################
    # Internal cache
    ####################################################################

    def _cached(
        self,
        key: str,
        calculation: Callable
    ):

        if key not in self._cache:

            self._cache[key] = calculation()

        return self._cache[key]
    
        ####################################################################
    # Geometry
    ####################################################################

    @property
    def number_of_components(self) -> int:

        return len(self.bha.components)

    @property
    def total_length(self) -> float:

        return self._cached(

            "total_length",

            lambda: sum(

                component.length_ft

                for component in self.bha.components

            )

        )

    @property
    def total_weight(self) -> float:

        return self._cached(

            "total_weight",

            lambda: sum(

                component.weight_lb

                for component in self.bha.components

            )

        )

    @property
    def average_component_weight(self) -> float:

        if self.number_of_components == 0:

            return 0.0

        return (

            self.total_weight

            / self.number_of_components

        )
    
        ####################################################################
    # Weight Distribution
    ####################################################################

    @property
    def collar_weight(self) -> float:

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
    def hwdp_weight(self) -> float:

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
    def drillpipe_weight(self) -> float:

        return self._cached(

            "drillpipe_weight",

            lambda: sum(

                component.weight_lb

                for component in self.bha.components

                if component.component_type
                == ComponentType.DRILL_PIPE

            )

        )
    
      ####################################################################
    # Weight On Bit (WOB)
    ####################################################################

    @property
    def available_wob(self) -> float:
        """
        Maximum available Weight on Bit (lb).

        Uses only drill collar weight multiplied by the
        buoyancy factor.
        """

        return self._cached(

            "available_wob",

            lambda:

            self.collar_weight
            * constants.DEFAULT_BUOYANCY_FACTOR

        )

    @property
    def recommended_wob(self) -> float:
        """
        Recommended WOB based on hole size.

        Future versions will also consider:

        - Formation UCS
        - Bit Type
        - Cutter Size
        - Bit Manufacturer
        - Formation Abrasiveness
        """

        def calculate():

            bit = self.bha.bit

            if bit is None:

                return 0.0

            diameter = bit.outer_diameter_in

            if diameter >= 17.0:

                return constants.VERTICAL_WOB_LB

            elif diameter >= 12.0:

                return constants.BUILD_SECTION_WOB_LB

            elif diameter >= 8.0:

                return constants.HORIZONTAL_WOB_LB

            else:

                return constants.SMALL_HOLE_WOB_LB

        return self._cached(

            "recommended_wob",

            calculate

        )

    @property
    def wob_utilization(self) -> float:
        """
        Percentage of available WOB currently required.
        """

        if self.available_wob == 0:

            return 0.0

        return (

            self.recommended_wob

            / self.available_wob

        )

    @property
    def excess_wob(self) -> float:
        """
        Remaining available WOB.
        """

        return (

            self.available_wob

            - self.recommended_wob

        )

    @property
    def wob_reserve_percent(self) -> float:
        """
        Remaining WOB expressed as percentage.
        """

        if self.available_wob == 0:

            return 0.0

        return (

            self.excess_wob

            / self.available_wob

        ) * 100.0

            ####################################################################
    # WOB Classification
    ####################################################################

    @property
    def wob_status(self) -> str:

        utilization = self.wob_utilization

        if utilization <= 0.60:

            return "Underloaded"

        elif utilization <= constants.MAX_WOB_UTILIZATION:

            return "Optimal"

        elif utilization <= 1.00:

            return "High"

        else:

            return "Overloaded"

            ####################################################################
    # Neutral Point
    ####################################################################

    @property
    def neutral_point(self) -> float:
        """
        Neutral point measured from the bit.

        Units:
            ft
        """

        def calculate():

            collar_length = sum(

                component.length_ft

                for component in self.bha.components

                if component.component_type
                == ComponentType.DRILL_COLLAR

            )

            if self.collar_weight == 0:

                return 0.0

            return (

                self.recommended_wob

                / self.collar_weight

            ) * collar_length

        return self._cached(

            "neutral_point",

            calculate

        )
    
    ####################################################################
    # Hydraulics
    ####################################################################

    @property
    def hydraulic_horsepower(self) -> float:
        """
        Surface Hydraulic Horsepower (HHP).
        """

        return self._cached(
            "hydraulic_horsepower",
            lambda: (
                self.bha.flow_rate_gpm
                * self.bha.pump_pressure_psi
            ) / 1714
        )

    @property
    def bit_hydraulic_horsepower(self) -> float:
        """
        Hydraulic Horsepower at the bit.
        """

        return self._cached(
            "bit_hydraulic_horsepower",
            lambda: (
                self.bha.flow_rate_gpm
                * self.bha.bit_pressure_loss_psi
            ) / 1714
        )

    @property
    def hydraulic_efficiency(self) -> float:

        if self.hydraulic_horsepower == 0:
            return 0.0

        return (
            self.bit_hydraulic_horsepower
            / self.hydraulic_horsepower
        )

    @property
    def jet_velocity(self) -> float:
        """
        Jet velocity (ft/s).
        """

        if self.bha.nozzle_area_in2 == 0:
            return 0.0

        return (
            0.3208
            * self.bha.flow_rate_gpm
            / self.bha.nozzle_area_in2
        )

    @property
    def hydraulic_hsi(self) -> float:
        """
        Hydraulic Horsepower per Square Inch.
        """

        if self.bha.bit is None:
            return 0.0

        bit_area = (
            pi * self.bha.bit.outer_diameter_in ** 2
        ) / 4

        if bit_area == 0:
            return 0.0

        return (
            self.bit_hydraulic_horsepower
            / bit_area
        )

    @property
    def cleaning_index(self) -> float:

        return (
            self.jet_velocity
            * self.hydraulic_efficiency
        ) / 100

    @property
    def hydraulics_status(self) -> str:

        index = self.cleaning_index

        if index < 0.40:
            return "Poor"

        elif index < 0.70:
            return "Fair"

        elif index < 1.00:
            return "Good"

        return "Excellent"
    
####################################################################
# Buckling
####################################################################

    @property
    def compressive_load(self) -> float:
        """
        Current compressive force.

        Approximated as Recommended WOB.
        """

        return self.recommended_wob

    @property
    def critical_sinusoidal_load(self) -> float:
        """
        Approximate sinusoidal buckling load (lbf).

        Simplified engineering equation.
        """

        collar_weight = self.collar_weight

        if collar_weight == 0:
            return 0.0

        return collar_weight * 0.60

    @property
    def critical_helical_load(self) -> float:
        """
        Approximate helical buckling load.
        """

        collar_weight = self.collar_weight

        if collar_weight == 0:
            return 0.0

        return collar_weight * 0.90

    @property
    def buckling_safety_factor(self) -> float:

        critical = self.critical_helical_load

        if critical == 0:
            return 0.0

        return critical / self.compressive_load

    @property
    def compression_ratio(self) -> float:

        critical = self.critical_sinusoidal_load

        if critical == 0:
            return 0.0

        return self.compressive_load / critical
  
    @property
    def buckling_status(self) -> str:

        ratio = self.compression_ratio

        if ratio < 0.80:
            return "Stable"

        elif ratio < 1.00:
            return "Near Sinusoidal"

        elif ratio < 1.50:
            return "Sinusoidal"

        return "Helical"
    
    @property
    def buckling_recommendation(self) -> str:

        status = self.buckling_status

        if status == "Stable":
            return "No action required."

        elif status == "Near Sinusoidal":
            return "Monitor WOB."

        elif status == "Sinusoidal":
            return "Reduce WOB or increase collar stiffness."

        return "High buckling risk. Redesign BHA."
    
    @property
    def collar_length(self) -> float:

        return sum(

            component.length_ft

            for component in self.bha.components

            if component.component_type == ComponentType.DRILL_COLLAR

        )


    @property
    def average_collar_od(self) -> float:

        collars = [

            component.outer_diameter_in

            for component in self.bha.components

            if component.component_type == ComponentType.DRILL_COLLAR

        ]

        return mean(collars) if collars else 0.0


    @property
    def average_collar_id(self) -> float:

        collars = [

            component.inner_diameter_in

            for component in self.bha.components

            if component.component_type == ComponentType.DRILL_COLLAR

        ]

        return mean(collars) if collars else 0.0

    @property
    def collar_inertia(self) -> float:

        od = self.average_collar_od
        id_ = self.average_collar_id

        if od == 0:
            return 0.0

        return (

            math.pi / 64

        ) * (

            od**4 - id_**4

        )

    @property
    def euler_load(self) -> float:

        if self.collar_length == 0:
            return 0.0

        E = YOUNGS_MODULUS_STEEL_PSI

        I = self.collar_inertia

        L = self.collar_length * 12

        return (

            math.pi**2

            * E

            * I

        ) / (

            L**2

        )

    @property
    def critical_sinusoidal_load(self):

        return 0.80 * self.euler_load

    @property
    def critical_helical_load(self):

        return self.euler_load

    @property
    def buckling_status(self):

        ratio = self.compression_ratio

        if ratio < 0.8:
            return "Stable"

        elif ratio < 1.0:
            return "Approaching Sinusoidal"

        elif ratio < 1.3:
            return "Sinusoidal"

        else:
            return "Helical"
    
