from __future__ import annotations

from dataclasses import dataclass, field
from math import pi


@dataclass(slots=True)
class MechanicalSpecificEnergy:
    """
    Mechanical Specific Energy (Professional)

    Engineering Suite v4.2
    """

    # Identification
    well_name: str = ""
    bit_number: int = 1
    bit_type: str = ""

    # Bit
    bit_diameter_in: float = 12.25

    # Drilling Parameters
    wob_klbf: float = 0.0
    torque_ftlb: float = 0.0
    rpm: float = 0.0
    rop_ft_hr: float = 0.0

    # Hydraulics
    flow_rate_gpm: float = 0.0
    standpipe_pressure_psi: float = 0.0

    # Mud
    mud_weight_ppg: float = 0.0

    # Formation
    ucs_psi: float | None = None

    # Downhole Motor
    motor_torque_ftlb: float = 0.0

    # Optional optimization target
    target_mse: float | None = None

    recommendations: list[str] = field(default_factory=list)

    @property
    def bit_area(self):

        return pi * self.bit_diameter_in**2 / 4

    @property
    def effective_torque(self):

        return self.torque_ftlb + self.motor_torque_ftlb

    @property
    def axial_energy(self):

        return (self.wob_klbf * 1000) / self.bit_area

    @property
    def rotary_energy(self):

        if self.rop_ft_hr <= 0:

            return 0

        return (

            120

            * pi

            * self.effective_torque

            * self.rpm

        ) / (

            self.bit_area

            * self.rop_ft_hr

        )

    @property
    def mse(self):

        return self.axial_energy + self.rotary_energy

    @property
    def mse_ratio(self):

        if self.ucs_psi is None:

            return None

        return self.mse / self.ucs_psi

    @property
    def efficiency(self):

        if self.ucs_psi is None:

            if self.mse < 15000:
                return "Excellent"

            elif self.mse < 25000:
                return "Good"

            elif self.mse < 35000:
                return "Fair"

            return "Poor"

        ratio = self.mse_ratio

        if ratio < 1.2:
            return "Excellent"

        elif ratio < 2:
            return "Good"

        elif ratio < 3:
            return "Fair"

        return "Poor"

    @property
    def optimization_recommendations(self):

        rec = []

        if self.rop_ft_hr < 20:

            rec.append(
                "Increase drilling efficiency."
            )

        if self.rpm > 220:

            rec.append(
                "RPM may be excessive."
            )

        if self.wob_klbf < 20:

            rec.append(
                "Increase WOB."
            )

        if self.mse > 40000:

            rec.append(
                "Review bit condition."
            )

        if self.ucs_psi:

            if self.mse_ratio > 3:

                rec.append(
                    "MSE significantly exceeds formation strength."
                )

        if not rec:

            rec.append(
                "Operating parameters are within expected limits."
            )

        return rec

    @property
    def summary(self):

        return {

            "Bit Area (in²)": round(self.bit_area,2),

            "Axial Energy": round(self.axial_energy,1),

            "Rotary Energy": round(self.rotary_energy,1),

            "Mechanical Specific Energy": round(self.mse,1),

            "Formation UCS": self.ucs_psi,

            "MSE Ratio": None if self.mse_ratio is None else round(self.mse_ratio,2),

            "Efficiency": self.efficiency,

            "Recommendations": self.optimization_recommendations,

        }