"""
==========================================================
Hydraulics Base

Engineering Suite v4.2
==========================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi


@dataclass(slots=True)
class HydraulicsBase:
    """
    Base class for all hydraulics calculations.
    """

    flow_rate_gpm: float
    pump_pressure_psi: float
    bit_diameter_in: float

    @property
    def bit_area(self) -> float:
        """
        Bit cross-sectional area (in²).
        """

        return pi * self.bit_diameter_in**2 / 4.0

    @property
    def hydraulic_horsepower(self) -> float:
        """
        Hydraulic Horsepower.
        """

        return (
            self.flow_rate_gpm
            * self.pump_pressure_psi
            / 1714.0
        )

    @property
    def hydraulic_intensity(self) -> float:
        """
        Hydraulic Horsepower per square inch.
        """

        return self.hydraulic_horsepower / self.bit_area