"""
==========================================================
Trip Speed Optimizer

Engineering Suite v4.2

Optimization Engine

Determines the maximum safe tripping speed
based on surge/swab constraints.

==========================================================
"""

from __future__ import annotations

from dataclasses import dataclass

@dataclass(slots=True)
class TripSpeedOptimizer:

    trip_speed_ft_min: float

    kick_margin_ppg: float

    fracture_margin_ppg: float

    window_utilization: float

    hydraulic_score: int

    @property
    def recommended_speed(self):

        speed = self.trip_speed_ft_min

        if self.kick_margin_ppg < 0.30:
            speed *= 0.80

        if self.fracture_margin_ppg < 1.00:
            speed *= 0.75

        if self.window_utilization > 70:
            speed *= 0.85

        return round(speed, 1)

    @property
    def speed_reduction(self):

        return round(

            self.trip_speed_ft_min

            -

            self.recommended_speed,

            1

        )

    @property
    def maximum_safe_speed(self):

        if self.kick_margin_ppg < 0.30:
            return round(self.trip_speed_ft_min * 0.85, 1)

        if self.fracture_margin_ppg < 1.0:
            return round(self.trip_speed_ft_min * 0.80, 1)

        return self.trip_speed_ft_min

    @property
    def speed_margin(self):

        margin = (
            self.maximum_safe_speed
            -
            self.recommended_speed
        )

        return round(margin,1)

    @property
    def operational_risk(self):

        if self.kick_margin_ppg < 0.20:
            return "HIGH"

        elif self.kick_margin_ppg < 0.30:
            return "MODERATE"

        return "LOW"

    @property
    def optimization_status(self):

        if self.speed_reduction == 0:

            return "OPTIMAL"

        elif self.speed_reduction < 15:

            return "MINOR ADJUSTMENT"

        elif self.speed_reduction < 30:

            return "REDUCE SPEED"

        return "SIGNIFICANT REDUCTION REQUIRED"

    @property
    def optimization_score(self):

        score = self.hydraulic_score

        if self.speed_reduction > 20:
            score -= 10

        return max(score, 0)

    @property
    def optimization_confidence(self):

        if self.hydraulic_score >= 90 and self.window_utilization < 50:
            return "HIGH"

        elif self.hydraulic_score >= 70:
            return "MEDIUM"

        return "LOW"

    @property
    def recommendations(self):

        rec = []

        if self.recommended_speed < self.trip_speed_ft_min:

            rec.append(

                f"Reduce trip speed to "

                f"{self.recommended_speed:.1f} ft/min."

            )

        else:

            rec.append(

                "Current trip speed is optimal."

            )

        if self.kick_margin_ppg < 0.30:

            rec.append(

                "Maintain additional kick surveillance."

            )

        if self.fracture_margin_ppg < 1.00:

            rec.append(

                "Monitor surge pressure closely."

            )

        return rec

    @property
    def executive_summary(self):

        if self.optimization_status == "OPTIMAL":

            return (

                "Current tripping speed is "

                "within the safe operating envelope."

            )

        return (

            f"Reduce tripping speed to "

            f"{self.recommended_speed:.1f} ft/min "

            "to preserve well control margins."

        )

    @property
    def summary(self):

        return {

            "Current Speed (ft/min)":
                self.trip_speed_ft_min,

            "Recommended Speed (ft/min)":
                self.recommended_speed,

            "Speed Reduction (ft/min)":
                self.speed_reduction,

            "Maximum Safe Speed (ft/min)":
                self.maximum_safe_speed,

            "Speed Margin (ft/min)": 
                self.speed_margin,

            "Operational Risk": 
                self.operational_risk,

            "Optimization Status":
                self.optimization_status,

            "Optimization Score":
                self.optimization_score,

            "Optimization Confidence": 
                self.optimization_confidence,

            "Recommendations":
                self.recommendations,

            "Executive Summary":
                self.executive_summary,

        }

    