"""
==========================================================
Hydraulic Horsepower per Square Inch (HSI)

Engineering Suite v4.2
==========================================================
"""

from __future__ import annotations

from .base import HydraulicsBase


class HydraulicHorsepowerPerSquareInch(HydraulicsBase):
    """
    Hydraulic Horsepower per Square Inch (HSI).
    """
    HSI_POOR = 2.0
    HSI_FAIR = 3.0
    HSI_GOOD = 5.0
    HSI_EXCELLENT = 7.0

    @property
    def hsi(self) -> float:
        return self.hydraulic_intensity

    @property
    def cleaning_efficiency(self):

        if self.hsi < self.HSI_POOR:
            return "Poor"

        elif self.hsi < self.HSI_FAIR:
            return "Fair"

        elif self.hsi < self.HSI_GOOD:
            return "Good"

        elif self.hsi < self.HSI_EXCELLENT:
            return "Excellent"

        return "Excessive"

    @property
    def recommended_range(self):

        return (
            f"{self.HSI_FAIR:.1f}"
            f" – "
            f"{self.HSI_GOOD:.1f} HSI"
    )

    @property
    def hydraulic_score(self):

        if self.hsi < self.HSI_POOR:
            return 20

        elif self.hsi < self.HSI_FAIR:
            return 50

        elif self.hsi <= self.HSI_GOOD:
            return 100

        elif self.hsi <= self.HSI_EXCELLENT:
            return 90

        return 60

    @property
    def status(self):

        if self.hsi < self.HSI_POOR:
            return "RED"

        elif self.hsi < self.HSI_FAIR:
            return "YELLOW"

        elif self.hsi <= self.HSI_GOOD:
            return "GREEN"

        elif self.hsi <= self.HSI_EXCELLENT:
            return "BLUE"

        return "ORANGE"

    def validate(self):

        if self.flow_rate_gpm <= 0:
            raise ValueError("Flow rate must be positive.")

        if self.pump_pressure_psi <= 0:
            raise ValueError("Pump pressure must be positive.")

        if self.bit_diameter_in <= 0:
            raise ValueError("Bit diameter must be positive.")

    @property
    def recommendations(self):

        if self.hsi < self.HSI_POOR:
            return [
                "Increase pump flow rate.",
                "Increase pump pressure.",
                "Review nozzle sizing.",
            ]

        elif self.hsi < self.HSI_FAIR:
            return [
                "Hydraulics are marginal.",
                "Consider nozzle optimization.",
            ]

        elif self.hsi <= self.HSI_GOOD:
            return [
                "Hydraulic intensity is within the optimum range.",
            ]

        elif self.hsi <= self.HSI_EXCELLENT:
            return [
                "Excellent hydraulic cleaning.",
            ]

        return [
            "Hydraulic intensity exceeds recommended range.",
            "Inspect bit nozzles for erosion.",
        ]

    @property
    def summary(self):

        return {

            "Flow Rate (gpm)": self.flow_rate_gpm,

            "Pump Pressure (psi)": self.pump_pressure_psi,

            "Bit Diameter (in)": self.bit_diameter_in,

            "Bit Area (in²)": round(self.bit_area, 2),

            "Hydraulic Horsepower": round(
                self.hydraulic_horsepower, 1
            ),

            "HSI": round(self.hsi, 2),

            "Hydraulic Score": self.hydraulic_score,

            "Status": self.status,

            "Cleaning Efficiency": self.cleaning_efficiency,

            "Recommended Range": self.recommended_range,

            "Recommendations": self.recommendations,

        }