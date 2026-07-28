from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BitPerformance:
    """
    Bit Performance Analytics

    Engineering Suite v4.2
    """

    bit_number: int
    bit_type: str
    manufacturer: str

    footage_ft: float
    drilling_hours: float
    rotating_hours: float

    bit_cost_usd: float

    iadc_dull_grade: str = ""

    @property
    def average_rop(self):

        if self.drilling_hours == 0:
            return 0.0

        return self.footage_ft / self.drilling_hours

    @property
    def mechanical_rop(self):

        if self.rotating_hours == 0:
            return 0.0

        return self.footage_ft / self.rotating_hours

    @property
    def cost_per_foot(self):

        if self.footage_ft == 0:
            return 0.0

        return self.bit_cost_usd / self.footage_ft

    @property
    def cost_per_hour(self):

        if self.drilling_hours == 0:
            return 0.0

        return self.bit_cost_usd / self.drilling_hours

    @property
    def utilization(self):

        if self.drilling_hours == 0:
            return 0.0

        return (
            self.rotating_hours
            / self.drilling_hours
            * 100
        )

    @property
    def recommendation(self):

        if self.cost_per_foot < 20:
            return "Continue using this bit model"

        if self.cost_per_foot < 40:
            return "Monitor performance"

        return "Review bit selection"

    @property
    def summary(self):

        return {
            "Bit Number": self.bit_number,
            "Manufacturer": self.manufacturer,
            "Bit Type": self.bit_type,
            "Footage (ft)": round(self.footage_ft, 1),
            "Average ROP": round(self.average_rop, 2),
            "Mechanical ROP": round(self.mechanical_rop, 2),
            "Cost per Foot": round(self.cost_per_foot, 2),
            "Cost per Hour": round(self.cost_per_hour, 2),
            "Utilization %": round(self.utilization, 1),
            "IADC Grade": self.iadc_dull_grade,
            "Recommendation": self.recommendation,
        }

    