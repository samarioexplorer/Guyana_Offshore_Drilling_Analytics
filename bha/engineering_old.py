"""
========================================================================
BHA Engineering Suite v2.1

engineering.py

Professional engineering calculation engine for
Bottom Hole Assemblies.

Author : Anibal Ceballos
========================================================================
"""

from __future__ import annotations

from math import pi
from statistics import mean

from .assembly import BottomHoleAssembly
from .enums import ComponentType
from . import constants


class BHAEngineering:
    """
    Professional engineering calculation engine.

    One instance analyzes one Bottom Hole Assembly.

    Example
    -------
    >>> eng = BHAEngineering(bha)
    >>> eng.total_weight
    >>> eng.available_wob
    >>> eng.engineering_score
    """

    ####################################################################
    # CONSTRUCTOR
    ####################################################################

    def __init__(
        self,
        bha: BottomHoleAssembly
    ) -> None:

        self.bha = bha

        self._cache = {}

    ####################################################################
    # CACHE
    ####################################################################

    def clear_cache(self) -> None:
        """
        Clears every cached engineering value.
        """

        self._cache.clear()

    ####################################################################
    # INTERNAL CACHE
    ####################################################################

    def _cached(
        self,
        key,
        calculation
    ):

        if key not in self._cache:

            self._cache[key] = calculation()

        return self._cache[key]
    
    ####################################################################
# GEOMETRY
####################################################################

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
def number_of_components(self) -> int:

    return len(self.bha.components)

####################################################################
# STRING WEIGHT
####################################################################

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

####################################################################
# CENTER OF GRAVITY
####################################################################

@property
def center_of_gravity(self):

    def calculate():

        depth = 0.0

        moment = 0.0

        total_weight = 0.0

        for component in self.bha.components:

            midpoint = depth + component.length_ft / 2

            moment += midpoint * component.weight_lb

            total_weight += component.weight_lb

            depth += component.length_ft

        if total_weight == 0:

            return 0.0

        return moment / total_weight

    return self._cached(

        "center_of_gravity",

        calculate

    )

####################################################################
# STIFFNESS
####################################################################

@property
def stiffness_index(self):

    def calculate():

        diameters = [

            component.od

            for component in self.bha.components

            if component.component_type in (

                ComponentType.DRILL_COLLAR,

                ComponentType.HWDP

            )

        ]

        if not diameters:

            return 0.0

        return mean(

            diameter ** 4

            for diameter in diameters

        )

    return self._cached(

        "stiffness",

        calculate

    )

####################################################################
# WEIGHT ON BIT (WOB)
####################################################################

@property
def available_wob(self) -> float:
    """
    Conservative available Weight on Bit (lb).

    Uses buoyancy factor from constants.py.
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
    Recommended Weight on Bit.

    Based on bit diameter.
    """

    def calculate():

        if self.bha.bit is None:
            return 0.0

        diameter = self.bha.bit.diameter_in

        if diameter >= 17.0:
            return constants.VERTICAL_WOB_LB

        if diameter >= 12.0:
            return constants.BUILD_SECTION_WOB_LB

        if diameter >= 8.0:
            return constants.HORIZONTAL_WOB_LB

        return constants.SMALL_HOLE_WOB_LB

    return self._cached(

        "recommended_wob",

        calculate

    )


@property
def wob_utilization(self) -> float:
    """
    Ratio between recommended and available WOB.
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
    Positive value means additional WOB
    is available.
    """

    return (

        self.available_wob

        - self.recommended_wob

    )

####################################################################
# NEUTRAL POINT
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
# WOB STATUS
####################################################################

@property
def wob_status(self) -> str:

    utilization = self.wob_utilization

    if utilization < 0.60:

        return "Underloaded"

    if utilization < constants.MAX_WOB_UTILIZATION:

        return "Optimal"

    if utilization < 1.00:

        return "High"

    return "Overloaded"

####################################################################
# WOB RESERVE
####################################################################

@property
def wob_reserve_percent(self):

    if self.available_wob == 0:

        return 0.0

    return (

        self.excess_wob

        / self.available_wob

    ) * 100.0

if __name__ == "__main__":

    print("BHA Engineering Suite v2.1")

    print("This module is intended to be imported.")

    print("Run test_engineering.py for examples.")

    