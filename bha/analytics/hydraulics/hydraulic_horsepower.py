from __future__ import annotations

from .base import HydraulicsBase


class HydraulicHorsepower(HydraulicsBase):
    """
    Hydraulic Horsepower calculator.
    """

    @property
    def hhp(self):
        return self.hydraulic_horsepower

    @property
    def rating(self):

        if self.hhp < 300:
            return "Poor"

        elif self.hhp < 600:
            return "Fair"

        elif self.hhp < 1000:
            return "Good"

        return "Excellent"

    @property
    def recommendations(self):

        if self.rating == "Poor":
            return [
                "Increase flow rate.",
                "Increase pump pressure.",
            ]

        if self.rating == "Fair":
            return [
                "Hydraulics could be improved.",
            ]

        return [
            "Hydraulic system operating within expected range.",
        ]

    @property
    def summary(self):

        return {

            "Flow Rate (gpm)": self.flow_rate_gpm,

            "Pump Pressure (psi)": self.pump_pressure_psi,

            "Bit Diameter (in)": self.bit_diameter_in,

            "Bit Area (in²)": round(self.bit_area, 2),

            "Hydraulic Horsepower": round(self.hhp, 1),

            "Rating": self.rating,

            "Recommendations": self.recommendations,

        }