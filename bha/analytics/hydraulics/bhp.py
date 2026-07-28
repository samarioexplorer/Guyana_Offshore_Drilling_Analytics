"""
==========================================================
Bottom-Hole Pressure Engine

Engineering Suite v4.2
==========================================================
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BottomHolePressure:

    mud_weight_ppg: float

    tvd_ft: float

    annular_pressure_loss_psi: float = 0

    surge_pressure_psi: float = 0

    swab_pressure_psi: float = 0

    pore_pressure_ppg: float = 0

    fracture_gradient_ppg: float = 0

    PSI_PER_PPG_FT = 0.052

    @property
    def hydrostatic_pressure(self):

        return (
            self.PSI_PER_PPG_FT
            * self.mud_weight_ppg
            * self.tvd_ft
        )

    @property
    def circulating_bhp(self):

        return (
            self.hydrostatic_pressure
            + self.annular_pressure_loss_psi
        )

    @property
    def surge_bhp(self):

        return (
            self.hydrostatic_pressure
            + self.surge_pressure_psi
        )

    @property
    def swab_bhp(self):

        return (
            self.hydrostatic_pressure
            - self.swab_pressure_psi
        )

    @property
    def circulating_density(self):

        return (

            self.circulating_bhp

            /

            (self.PSI_PER_PPG_FT * self.tvd_ft)

        )

    @property
    def surge_density(self):

        return (

            self.surge_bhp

            /

            (self.PSI_PER_PPG_FT * self.tvd_ft)

        )

    @property
    def swab_density(self):

        return (

            self.swab_bhp

            /

            (self.PSI_PER_PPG_FT * self.tvd_ft)

        )

    @property
    def kick_margin(self):

        if self.pore_pressure_ppg == 0:
            return None

        return (

            self.swab_density

            - self.pore_pressure_ppg

        )

    @property
    def fracture_margin(self):

        if self.fracture_gradient_ppg == 0:
            return None

        return (

            self.fracture_gradient_ppg

            - self.surge_density

        )

    @property
    def pressure_window_status(self):

        if self.kick_margin is not None:

            if self.kick_margin < 0:

                return "UNDERBALANCED"

        if self.fracture_margin is not None:

            if self.fracture_margin < 0:

                return "FRACTURE RISK"

        if (
            self.kick_margin is not None
            and self.fracture_margin is not None
        ):

            if self.kick_margin < 0.20:

                return "NARROW WINDOW"

        return "SAFE"

    @property
    def bhp_score(self):

        if self.pressure_window_status == "SAFE":
            return 100

        elif self.pressure_window_status == "NARROW WINDOW":
            return 80

        elif self.pressure_window_status == "UNDERBALANCED":
            return 40

        return 20

    @property
    def well_control_risk(self):

        if self.kick_margin is None:
            return "UNKNOWN"

        if self.kick_margin >= 0.50:
            return "LOW"

        elif self.kick_margin >= 0.20:
            return "MODERATE"

        elif self.kick_margin >= 0:
            return "HIGH"

        return "CRITICAL"

    @property
    def loss_risk(self):

        if self.fracture_margin is None:
            return "UNKNOWN"

        if self.fracture_margin >= 1.5:
            return "LOW"

        elif self.fracture_margin >= 1.0:
            return "MODERATE"

        elif self.fracture_margin >= 0:
            return "HIGH"

        return "SEVERE"

    @property
    def status(self):

        if self.pressure_window_status == "SAFE":
            return "GREEN"

        elif self.pressure_window_status == "NARROW WINDOW":
            return "YELLOW"

        elif self.pressure_window_status == "UNDERBALANCED":
            return "ORANGE"

        return "RED"

    @property
    def summary(self):

        return {

            "Hydrostatic Pressure (psi)":
                round(self.hydrostatic_pressure,1),

            "Circulating BHP (psi)":
                round(self.circulating_bhp,1),

            "Surge BHP (psi)":
                round(self.surge_bhp,1),

            "Swab BHP (psi)":
                round(self.swab_bhp,1),

            "Circulating Density (ppg)":
                round(self.circulating_density,2),

            "Surge Density (ppg)":
                round(self.surge_density,2),

            "Swab Density (ppg)":
                round(self.swab_density,2),

           "Kick Margin (ppg)": (round(self.kick_margin, 2)
            if self.kick_margin is not None
            else None),

            "Fracture Margin (ppg)": (round(self.fracture_margin, 2)
             if self.fracture_margin is not None
             else None),

            "BHP Score": self.bhp_score,

            "Well Control Risk": self.well_control_risk,

            "Loss Risk": self.loss_risk,

            "Pressure Window": self.pressure_window_status
        }