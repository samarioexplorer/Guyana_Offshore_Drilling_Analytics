"""
==========================================================
Pressure Window Analyzer

Engineering Suite v4.2

Integrated Well Pressure Decision Engine
==========================================================
"""

from __future__ import annotations

from dataclasses import dataclass

from datetime import datetime

@dataclass(slots=True)
class PressureWindowAnalyzer:

    pore_pressure_ppg: float

    fracture_gradient_ppg: float

    mud_weight_ppg: float

    ecd_ppg: float

    surge_density_ppg: float

    swab_density_ppg: float

    @property
    def kick_margin(self):

        return self.swab_density_ppg - self.pore_pressure_ppg

    @property
    def fracture_margin(self):

        return self.fracture_gradient_ppg - self.surge_density_ppg

    @property
    def window_width(self):

        return (

            self.fracture_gradient_ppg

            -

            self.pore_pressure_ppg

        )

    @property
    def window_utilization(self):

        used = (

            self.ecd_ppg

            -

            self.pore_pressure_ppg

        )

        return max(

            0,

            min(

                100,

                used

                /

                self.window_width

                * 100

            )

        )

    @property
    def available_window(self):

        return (

            self.fracture_gradient_ppg

            -

            self.pore_pressure_ppg

        )

    @property
    def pressure_window(self):

        if self.swab_density_ppg < self.pore_pressure_ppg:

            return "UNDERBALANCED"

        if self.surge_density_ppg > self.fracture_gradient_ppg:

            return "FRACTURE RISK"

        if self.kick_margin < 0.20:

            return "NARROW WINDOW"

        return "SAFE"

    @property
    def hydraulic_score(self):

        score = 100

        if self.kick_margin < 0.30:
            score -= 10

        if self.fracture_margin < 1.00:
            score -= 15

        if self.window_utilization > 70:
            score -= 10

        return max(score, 0)

    @property
    def safety_factor(self):

        if self.available_window == 0:
            return 0

        return (

            self.kick_margin

            /

            self.available_window

        )

    @property
    def status(self):

        if self.hydraulic_score >= 90:
            return "GREEN"

        elif self.hydraulic_score >= 75:
            return "YELLOW"

        elif self.hydraulic_score >= 50:
            return "ORANGE"

        return "RED"

    @property
    def severity(self):

        if self.status == "GREEN":
            return "NORMAL"

        elif self.status == "YELLOW":
            return "CAUTION"

        elif self.status == "ORANGE":
            return "WARNING"

        return "CRITICAL"

    @property
    def window_utilization_class(self):

        utilization = self.window_utilization

        if utilization < 40:
            return "COMFORTABLE"

        elif utilization < 70:
            return "MODERATE"

        elif utilization < 90:
            return "NARROW"

        return "CRITICAL"

    @property
    def operating_envelope(self):

        return {

            "Lower Limit": self.pore_pressure_ppg,

            "Current MW": self.mud_weight_ppg,

            "ECD": self.ecd_ppg,

            "Upper Limit": self.fracture_gradient_ppg

        }

    @property
    def pressure_margin_percent(self):

        return (

            self.kick_margin

            /

            self.available_window

            * 100

        )

    @property
    def risk_index(self):

        risk = 0

        if self.kick_margin < 0.30:
            risk += 35

        if self.fracture_margin < 1.00:
            risk += 35

        if self.window_utilization > 70:
            risk += 30

        return min(risk, 100)

    @property
    def recommendations(self):

        rec = []

        if self.window_utilization > 80:

            rec.append(
                "Consider reducing flow rate."
            )

        if self.kick_margin < 0.30:

            rec.append(
                "Kick margin is becoming narrow."
            )

        if self.fracture_margin < 1.0:

            rec.append(
                "Approaching fracture gradient."
            )

        if not rec:

            rec.extend([

                "Continue drilling.",

                "Hydraulic window acceptable.",

                "Maintain current mud weight."

            ])

        return rec

    @property
    def executive_summary(self):
    
            if self.pressure_window == "SAFE":
    
                if self.kick_margin < 0.30:
    
                    return (
                        "Pressure window remains safe. "
                        "Kick margin is becoming narrow; "
                        "continue drilling while monitoring ECD and trip operations."
                    )
    
                return (
                    "Pressure window is comfortable. "
                    "Current drilling parameters are within design limits."
                )
    
            if self.pressure_window == "UNDERBALANCED":
    
                return (
                    "Immediate attention required. "
                    "Increase effective bottom-hole pressure."
                )
    
            return (
                "Approaching fracture limit. "
                "Reduce hydraulic loading and review circulation parameters."
            )

    @property
    def summary(self):

            return {

                "Module": "Pressure Window Analyzer",

                "Version": "2.0",

                "Engineering Suite": "v4.2",

                "API Reference": "Pressure Window Analysis",

                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

                "Pore Pressure (ppg)":
                    round(self.pore_pressure_ppg, 2),

                "Mud Weight (ppg)":
                    round(self.mud_weight_ppg, 2),

                "ECD (ppg)":
                    round(self.ecd_ppg, 2),

                "Surge Density (ppg)":
                    round(self.surge_density_ppg, 2),

                "Swab Density (ppg)":
                    round(self.swab_density_ppg, 2),

                "Fracture Gradient (ppg)":
                    round(self.fracture_gradient_ppg, 2),

                "Kick Margin (ppg)":
                    round(self.kick_margin, 2),

                "Fracture Margin (ppg)":
                    round(self.fracture_margin, 2),

                "Pressure Window":
                    self.pressure_window,

                "Window Utilization (%)":
                    round(self.window_utilization, 1),

                "Available Window (ppg)":
                round(self.available_window,2),

                "Safety Factor":
                round(self.safety_factor,2),

                "Hydraulic Score":
                    self.hydraulic_score,

                "Status":
                    self.status,

                "Severity": 
                    self.severity,

                "Recommendations":
                    self.recommendations,

                "Window Utilization (%)":
                round(self.window_utilization,1),

                "Window Classification":
                    self.window_utilization_class,

                "Executive Summary": 
                    self.executive_summary,
            }

    

