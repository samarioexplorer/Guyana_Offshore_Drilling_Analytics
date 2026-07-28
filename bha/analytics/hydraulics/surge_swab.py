"""
==========================================================
Surge & Swab Analysis

Engineering Suite v4.2

Dynamic Wellbore Pressure During Pipe Movement

Author: Engineering Suite
==========================================================
"""

from __future__ import annotations

"""
    Surge & Swab Pressure Analysis

    Estimates the transient pressure generated during
    pipe movement inside the wellbore.

    Pipe moving IN  -> Surge Pressure

    Pipe moving OUT -> Swab Pressure

    Version 1 uses an engineering empirical model.

    Future versions will support:

        • Bingham Plastic

        • Herschel-Bulkley

        • Power Law

        • API RP 13D

        • Multiple hole sections

        • Real-time modeling
    """

# ---------------------------------------------------------
# Engineering Constants
# ---------------------------------------------------------



from dataclasses import dataclass

@dataclass(slots=True)
class SurgeSwabAnalysis:

        #
        # Empirical Surge/Swab coefficient
        #
        EMPIRICAL_COEFFICIENT = 0.015

        #
        # Pressure conversion
        #

        PSI_PER_PPG_FT = 0.052

        #
        # Rating thresholds
        #

        EXCELLENT_LIMIT = 0.20
        GOOD_LIMIT = 0.40
        FAIR_LIMIT = 0.70

        #
        # Traffic-light thresholds
        #

        LOW_RISK = 0.20
        MODERATE_RISK = 0.50
        HIGH_RISK = 0.80

        #
        # Pipe directions
        #
        RUN_IN = "IN"

        PULL_OUT = "OUT"

        # Recommended trip speeds (ft/min)

        MAX_SAFE_TRIP_SPEED = 120.0

        NORMAL_TRIP_SPEED = 90.0

        SLOW_TRIP_SPEED = 60.0

        mud_density_ppg: float

        plastic_viscosity_cp: float

        yield_point_lb100ft2: float

        trip_speed_ft_min: float

        pipe_od_in: float

        hole_id_in: float

        tvd_ft: float

        pipe_direction: str

        @property
        def pressure_change_psi(self):

                clearance = self.hole_id_in - self.pipe_od_in

                if clearance <= 0:
                    return 0

                k = 0.015

                return (

                    k

                    * self.plastic_viscosity_cp

                    * self.trip_speed_ft_min

                    * self.pipe_od_in

                    / clearance

                )

        @property
        def surge_pressure(self):

                if self.pipe_direction.upper() != "IN":
                    return 0

                return self.pressure_change_psi

        @property
        def swab_pressure(self):

                if self.pipe_direction.upper() != "OUT":
                    return 0

                return self.pressure_change_psi

        @property
        def equivalent_mud_weight(self):

                return (

                    self.pressure_change_psi

                    /

                    (0.052 * self.tvd_ft)

                )

        @property
        def rating(self):

            emw = self.equivalent_mud_weight

            if emw < 0.20:
                return "Excellent"

            elif emw < 0.40:
                return "Good"

            elif emw < 0.70:
                return "Fair"

            return "Poor"

        @property
        def well_control_risk(self):

            emw = self.equivalent_mud_weight

            if emw < 0.20:
                return "LOW"

            elif emw < 0.40:
                return "MODERATE"

            elif emw < 0.70:
                return "HIGH"

            return "CRITICAL"

        @property
        def status(self):

            risk = self.well_control_risk

            if risk == "LOW":
                return "GREEN"

            elif risk == "MODERATE":
                return "YELLOW"

            elif risk == "HIGH":
                return "ORANGE"

            return "RED"

        @property
        def surge_swab_score(self):

            emw = self.equivalent_mud_weight

            if emw < 0.20:
                return 100

            elif emw < 0.40:
                return 85

            elif emw < 0.70:
                return 65

            return 30

        @property
        def operation(self):

            if self.pipe_direction.upper() == self.RUN_IN:
                return "SURGE"

            return "SWAB"

        @property
        def recommendations(self):

            risk = self.well_control_risk

            if risk == "LOW":

                return [

                    "Pipe movement is within acceptable limits.",

                    "Continue tripping."

                ]

            elif risk == "MODERATE":

                return [

                    "Monitor trip speed.",

                    "Observe standpipe pressure."

                ]

            elif risk == "HIGH":

                return [

                    "Reduce trip speed.",

                    "Monitor equivalent mud weight.",

                    "Review well control margins."

                ]

            return [

                "Stop tripping.",

                "Excessive surge/swab pressure.",

                "Review hydraulic program immediately."
            ]

        @property
        def summary(self):

            return {

                "Operation": self.operation,

                "Trip Speed (ft/min)": self.trip_speed_ft_min,

                "Pressure Change (psi)": round(self.pressure_change_psi,1),

                "Equivalent Mud Weight (ppg)": round(
                    self.equivalent_mud_weight,2
                ),

                "Surge & Swab Score": self.surge_swab_score,

                "Hydraulic Rating": self.rating,

                "Well Control Risk": self.well_control_risk,

                "Status": self.status,

                "Recommendations": self.recommendations,

            }
