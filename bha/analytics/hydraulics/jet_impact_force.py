"""
==========================================================
Jet Impact Force (JIF)

Engineering Suite v4.2
==========================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi

from .base import HydraulicsBase


@dataclass(slots=True)
class JetImpactForce(HydraulicsBase):

    nozzle_diameter_in: float
    nozzle_count: int
    mud_density_ppg: float

    @property
    def total_nozzle_area(self):

        area = pi * self.nozzle_diameter_in**2 / 4.0

        return area * self.nozzle_count

    @property
    def jet_velocity(self):
        """
        Approximate jet velocity (ft/s)
        """

        if self.total_nozzle_area == 0:
            return 0.0

        return (
            0.321
            * self.flow_rate_gpm
            / self.total_nozzle_area
        )

    @property
    def jet_impact_force(self):
        """
        Simplified JIF (lbf)
        """

        return (
            0.01823
            * self.mud_density_ppg
            * self.flow_rate_gpm
            * self.jet_velocity
        )

    @property
    def rating(self):

        if self.jet_impact_force < 500:
            return "Poor"

        elif self.jet_impact_force < 1000:
            return "Fair"

        elif self.jet_impact_force < 2000:
            return "Good"

        return "Excellent"

    @property
    def recommendations(self):

        if self.rating == "Poor":
            return [
                "Increase hydraulic energy.",
                "Review nozzle sizing.",
            ]

        elif self.rating == "Fair":
            return [
                "Hydraulic cleaning could improve.",
            ]

        return [
            "Jet impact force is adequate.",
        ]

    @property
    def summary(self):

        return {

            "Flow Rate (gpm)": self.flow_rate_gpm,

            "Pump Pressure (psi)": self.pump_pressure_psi,

            "Mud Density (ppg)": self.mud_density_ppg,

            "Nozzle Count": self.nozzle_count,

            "Nozzle Diameter (in)": self.nozzle_diameter_in,

            "Jet Velocity (ft/s)": round(self.jet_velocity, 1),

            "Jet Impact Force (lbf)": round(
                self.jet_impact_force, 1
            ),

            "Rating": self.rating,

            "Recommendations": self.recommendations,

        }
    