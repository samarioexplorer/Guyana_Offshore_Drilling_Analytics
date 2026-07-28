"""
==========================================================
Pressure Loss Calculator

Engineering Suite v4.2
==========================================================
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import HydraulicsBase


@dataclass(slots=True)
class PressureLossCalculator(HydraulicsBase):

    drillpipe_length_ft: float
    drillpipe_id_in: float

    collar_length_ft: float
    collar_id_in: float

    annulus_hydraulic_diameter_in: float

    mud_density_ppg: float
    plastic_viscosity_cp: float
    yield_point_lb100ft2: float

    nozzle_pressure_loss_psi: float

    @property
    def drillpipe_pressure_loss(self):

        return (
            0.000020
            * self.flow_rate_gpm**2
            * self.drillpipe_length_ft
            / self.drillpipe_id_in**5
        )

    @property
    def drillcollar_pressure_loss(self):

        return (
            0.000018
            * self.flow_rate_gpm**2
            * self.collar_length_ft
            / self.collar_id_in**5
        )

    @property
    def annular_pressure_loss(self):

        return (
            0.000010
            * self.flow_rate_gpm**2
            * self.drillpipe_length_ft
            / self.annulus_hydraulic_diameter_in**4
        )

    @property
    def bit_pressure_loss(self):

        return self.nozzle_pressure_loss_psi

    @property
    def total_pressure_loss(self):

        return (

            self.drillpipe_pressure_loss

            + self.drillcollar_pressure_loss

            + self.annular_pressure_loss

            + self.bit_pressure_loss

        )

    @property
    def hydraulic_efficiency(self):

        if self.pump_pressure_psi == 0:
            return 0.0

        return (
            self.bit_pressure_loss
            / self.pump_pressure_psi
            * 100
        )

    @property
    def rating(self):

        eff = self.hydraulic_efficiency

        if eff < 45:
            return "Poor"

        elif eff < 55:
            return "Fair"

        elif eff < 65:
            return "Good"

        return "Excellent"

    @property
    def recommendations(self):

        if self.rating == "Poor":

            return [

                "Increase pressure available at the bit.",

                "Review nozzle sizing.",

                "Reduce unnecessary hydraulic losses.",

            ]

        elif self.rating == "Fair":

            return [

                "Hydraulic efficiency can be improved.",

            ]

        elif self.rating == "Good":

            return [

                "Hydraulic system operating efficiently.",

            ]

        return [

            "Excellent hydraulic energy transfer.",

        ]

    @property
    def summary(self):

        return {

            "Drill Pipe Loss (psi)": round(
                self.drillpipe_pressure_loss, 1
            ),

            "Drill Collar Loss (psi)": round(
                self.drillcollar_pressure_loss, 1
            ),

            "Annular Loss (psi)": round(
                self.annular_pressure_loss, 1
            ),

            "Bit Loss (psi)": round(
                self.bit_pressure_loss, 1
            ),

            "Total Circulating Pressure (psi)": round(
                self.total_pressure_loss, 1
            ),

            "Hydraulic Efficiency (%)": round(
                self.hydraulic_efficiency, 1
            ),

            "Rating": self.rating,

            "Recommendations": self.recommendations,

        }