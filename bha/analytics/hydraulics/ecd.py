"""
==========================================================
Equivalent Circulating Density (ECD)

Engineering Suite v4.2
==========================================================
"""

from __future__ import annotations

from dataclasses import dataclass

from .pressure_loss import PressureLossCalculator


@dataclass(slots=True)
class EquivalentCirculatingDensity(PressureLossCalculator):

    tvd_ft: float

    @property
    def ecd(self):

        if self.tvd_ft == 0:
            return self.mud_density_ppg

        return (

            self.mud_density_ppg

            +

            self.annular_pressure_loss

            /

            (0.052 * self.tvd_ft)

        )

    @property
    def ecd_increase(self):

        return self.ecd - self.mud_density_ppg

    @property
    def rating(self):

        increase = self.ecd_increase

        if increase < 0.20:
            return "Excellent"

        elif increase < 0.50:
            return "Good"

        elif increase < 0.80:
            return "Fair"

        return "Poor"

    @property
    def well_control_risk(self):

        increase = self.ecd_increase

        if increase < 0.30:
            return "LOW"

        elif increase < 0.60:
            return "MODERATE"

        elif increase < 1.00:
            return "HIGH"

        return "CRITICAL"

    @property
    def recommendations(self):

        risk = self.well_control_risk

        if risk == "LOW":

            return [
                "ECD increase is minimal.",
                "Hydraulics operating efficiently.",
            ]

        elif risk == "MODERATE":

            return [
                "Monitor annular pressure losses.",
                "Review flow rate during critical intervals.",
            ]

        elif risk == "HIGH":

            return [
                "High ECD may approach fracture pressure.",
                "Optimize hydraulics before increasing flow rate.",
                "Review nozzle configuration.",
            ]

        return [
            "Critical ECD increase detected.",
            "High risk of formation breakdown.",
            "Reduce circulation rate immediately.",
            "Evaluate well pressure window.",
        ]

    @property
    def summary(self):

        return {

            "Mud Weight (ppg)": self.mud_density_ppg,

            "Annular Pressure Loss (psi)": round(
                self.annular_pressure_loss,1
            ),

            "TVD (ft)": self.tvd_ft,

            "ECD (ppg)": round(self.ecd,2),

            "ECD Increase": round(
                self.ecd_increase,2
            ),

            "Hydraulic Rating": self.rating,

            "Well Control Risk": self.well_control_risk,

            "Recommendations": self.recommendations,

        }

    