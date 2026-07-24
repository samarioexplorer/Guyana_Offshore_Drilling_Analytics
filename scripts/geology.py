"""
======================================================================
GEOLOGY ENGINE

Guyana Offshore Drilling Analytics

Version 3.2

Author:
Anibal Ceballos

======================================================================

This module transforms the geological database into an engineering
engine capable of recommending drilling parameters.

No geological data is stored here.

All geological properties come from:

    geology_database.py

======================================================================
"""

from dataclasses import dataclass

import math

from geology_database import *

# ===============================================================
# ENGINE
# ===============================================================


class GeologyEngine:

    """
    Engineering engine.

    Reads the geological database and returns engineering
    recommendations.
    """

    def __init__(self):

        self.formations = FORMATIONS

    # ==========================================================
    # BASIC LOOKUPS
    # ==========================================================

    def formation(self, depth):

        return get_formation(depth)

    def formation_name(self, depth):

        return self.formation(depth).name

    def lithology(self, depth):

        return self.formation(depth).lithology

    def age(self, depth):

        return self.formation(depth).age

    def temperature(self, depth):

        return self.formation(depth).temperature

    def porosity(self, depth):

        return self.formation(depth).porosity

    def permeability(self, depth):

        return self.formation(depth).permeability

    def ucs(self, depth):

        return self.formation(depth).ucs

    def abrasiveness(self, depth):

        return self.formation(depth).abrasiveness
    
    # ==========================================================
    # PRESSURE ENGINEERING
    # ==========================================================

    def pore_pressure(self, depth):
        """
        Equivalent Mud Weight (EMW) pore pressure.
        """
        return self.formation(depth).pore_pressure


    def fracture_gradient(self, depth):
        """
        Equivalent Mud Weight fracture gradient.
        """
        return self.formation(depth).fracture_gradient


    def pressure_window(self, depth):
        """
        Available drilling pressure window (ppg).
        """
        formation = self.formation(depth)

        return round(
            formation.fracture_gradient -
            formation.pore_pressure,
            2
        )


    def recommended_mud_weight(self, depth):
        """
        Returns the middle of the safe drilling window.
        """

        formation = self.formation(depth)

        return round(

            (
                formation.mud_weight_min +
                formation.mud_weight_max
            ) / 2,

            2

        )


    def minimum_mud_weight(self, depth):

        return self.formation(depth).mud_weight_min


    def maximum_mud_weight(self, depth):

        return self.formation(depth).mud_weight_max


    def safe_mud_window(self, depth):

        formation = self.formation(depth)

        return (

            formation.mud_weight_min,

            formation.mud_weight_max

        )


    def kick_margin(self, mud_weight, depth):
        """
        Positive values indicate overbalanced drilling.
        """

        return round(

            mud_weight -

            self.pore_pressure(depth),

            2

        )


    def fracture_margin(self, mud_weight, depth):
        """
        Remaining margin before breaking down the formation.
        """

        return round(

            self.fracture_gradient(depth) -

            mud_weight,

            2

        )


    def equivalent_circulating_density(self,
                                       mud_weight,
                                       annular_loss):

        """
        Equivalent Circulating Density (ECD)

        annular_loss must be expressed as
        equivalent mud weight (ppg).
        """

        return round(

            mud_weight +

            annular_loss,

            2

        )


    def pressure_status(self,
                        mud_weight,
                        depth):
        """
        Returns drilling pressure condition.
        """

        kick = self.kick_margin(
            mud_weight,
            depth
        )

        frac = self.fracture_margin(
            mud_weight,
            depth
        )

        if kick < 0:

            return "UNDERBALANCED"

        elif frac < 0:

            return "BREAKDOWN"

        elif kick < 0.30:

            return "KICK RISK"

        elif frac < 0.30:

            return "LOSS RISK"

        else:

            return "SAFE"


    def pressure_summary(self, depth):
        """
        Returns a pressure summary dictionary.
        """

        mw = self.recommended_mud_weight(depth)

        return {

            "Pore Pressure":

                self.pore_pressure(depth),

            "Fracture Gradient":

                self.fracture_gradient(depth),

            "Mud Weight":

                mw,

            "Pressure Window":

                self.pressure_window(depth),

            "Kick Margin":

                self.kick_margin(mw, depth),

            "Fracture Margin":

                self.fracture_margin(mw, depth)

        }
    
    # ==========================================================
    # DRILLING ENGINEERING
    # ==========================================================

    def recommended_bit(self, depth):
        """
        Returns the recommended bit type.
        """

        return self.formation(depth).recommended_bit


    def recommended_bit_size(self, depth):
        """
        Returns the recommended bit size.
        """

        return self.formation(depth).recommended_bit_size


    def recommended_motor(self, depth):
        """
        Returns the recommended motor.
        """

        return self.formation(depth).recommended_motor


    def use_rss(self, depth):
        """
        Returns True when RSS is recommended.
        """

        return self.formation(depth).recommended_rss


    def recommended_rpm(self, depth):
        """
        Returns recommended RPM.
        """

        formation = self.formation(depth)

        return round(

            (

                formation.recommended_rpm_min +

                formation.recommended_rpm_max

            ) / 2,

            0

        )


    def recommended_rpm_range(self, depth):

        formation = self.formation(depth)

        return (

            formation.recommended_rpm_min,

            formation.recommended_rpm_max

        )


    def recommended_wob(self, depth):
        """
        Recommended Weight on Bit.
        """

        formation = self.formation(depth)

        return round(

            (

                formation.recommended_wob_min +

                formation.recommended_wob_max

            ) / 2,

            1

        )


    def recommended_wob_range(self, depth):

        formation = self.formation(depth)

        return (

            formation.recommended_wob_min,

            formation.recommended_wob_max

        )


    def recommended_flowrate(self, depth):
        """
        Recommended flow rate.
        """

        formation = self.formation(depth)

        return round(

            (

                formation.recommended_flowrate_min +

                formation.recommended_flowrate_max

            ) / 2,

            0

        )


    def recommended_flowrate_range(self, depth):

        formation = self.formation(depth)

        return (

            formation.recommended_flowrate_min,

            formation.recommended_flowrate_max

        )


    def expected_rop(self, depth):
        """
        Returns the formation expected ROP.
        """

        return self.formation(depth).expected_rop


    def drilling_difficulty(self, depth):
        """
        Returns drilling difficulty (0-100).
        """

        return self.formation(depth).drilling_difficulty


    def drilling_efficiency_factor(self, depth):
        """
        Efficiency factor used later for KPI calculations.
        """

        difficulty = self.drilling_difficulty(depth)

        factor = 1 - (difficulty / 140)

        return round(

            max(0.20, factor),

            2

        )


    def expected_connection_time(self, depth):
        """
        Connection time increases with depth.
        """

        formation = self.formation(depth)

        base = 0.35

        penalty = formation.drilling_difficulty / 250

        return round(

            base + penalty,

            2

        )


    def expected_reaming_probability(self, depth):
        """
        Probability that reaming will be required.
        """

        formation = self.formation(depth)

        probability = (

            formation.drilling_difficulty / 100

        ) * 0.75

        return round(

            min(probability, 0.95),

            2

        )


    def expected_sliding_ratio(self, depth):
        """
        Estimated percentage of sliding drilling.
        """

        if self.use_rss(depth):

            return 0.08

        motor = self.recommended_motor(depth)

        if motor == "Mud Motor":

            return 0.28

        if motor == "High Performance":

            return 0.18

        return 0.10


    def drilling_summary(self, depth):
        """
        Returns complete drilling recommendations.
        """

        return {

            "Formation":

                self.formation_name(depth),

            "Lithology":

                self.lithology(depth),

            "Bit":

                self.recommended_bit(depth),

            "Bit Size":

                self.recommended_bit_size(depth),

            "Motor":

                self.recommended_motor(depth),

            "RSS":

                self.use_rss(depth),

            "RPM":

                self.recommended_rpm(depth),

            "WOB":

                self.recommended_wob(depth),

            "Flow Rate":

                self.recommended_flowrate(depth),

            "ROP":

                self.expected_rop(depth),

            "Difficulty":

                self.drilling_difficulty(depth)

        }
    
    # ==========================================================
    # BIT PERFORMANCE ENGINE
    # ==========================================================

    def expected_bit_life(self, depth):
        """
        Expected bit life (hours).

        Adjusted according to formation abrasiveness
        and rock strength.
        """

        formation = self.formation(depth)

        life = formation.average_bit_life_hr

        abrasiveness_factor = 1 - (formation.abrasiveness * 0.45)

        ucs_factor = 1 - ((formation.ucs / 35000) * 0.35)

        return round(

            life *
            abrasiveness_factor *
            ucs_factor,

            1

        )


    def bit_wear(self,
                 bit_hours,
                 depth):
        """
        Returns estimated bit wear (%).
        """

        expected_life = self.expected_bit_life(depth)

        wear = (

            bit_hours /
            expected_life

        ) * 100

        wear = max(0, min(100, wear))

        return round(wear,1)


    def bit_efficiency(self,
                       bit_hours,
                       depth):
        """
        Bit cutting efficiency.
        """

        wear = self.bit_wear(
            bit_hours,
            depth
        )

        efficiency = 100 - wear

        return round(

            max(5, efficiency),

            1

        )


    def adjusted_rop(self,
                     bit_hours,
                     depth):
        """
        Expected ROP after bit wear.
        """

        base_rop = self.expected_rop(depth)

        efficiency = self.bit_efficiency(
            bit_hours,
            depth
        ) / 100

        return round(

            base_rop *
            efficiency,

            1

        )


    def dull_grade(self,
                   bit_hours,
                   depth):
        """
        Returns IADC dull grade.
        """

        wear = self.bit_wear(
            bit_hours,
            depth
        )

        if wear < 15:

            return "1-1-WT-A-X-I-NO-TD"

        elif wear < 35:

            return "2-2-WT-A-X-I-NO-TD"

        elif wear < 60:

            return "3-3-WT-A-X-I-BT-PR"

        elif wear < 85:

            return "4-4-WT-A-X-I-BT-WT"

        else:

            return "8-8-WT-X-X-X-TD"


    def pull_reason(self,
                    bit_hours,
                    depth):
        """
        Engineering pull reason.
        """

        wear = self.bit_wear(
            bit_hours,
            depth)

        if wear > 90:

            return "Bit Worn"

        if self.drilling_difficulty(depth) > 90:

            return "Motor Failure"

        if self.adjusted_rop(
                bit_hours,
                depth) < 30:

            return "Poor ROP"

        return "TD Reached"


    def bit_replacement_required(
            self,
            bit_hours,
            depth):

        wear = self.bit_wear(
            bit_hours,
            depth)

        return wear >= 85


    def expected_bit_cost(
            self,
            depth):

        bit = self.recommended_bit(depth)

        size = self.recommended_bit_size(depth)

        if bit == "Roller Cone":

            return 18000 + size * 450

        if bit == "Hybrid":

            return 42000 + size * 800

        return 65000 + size * 1200


    def bit_cost_per_hour(
            self,
            bit_hours,
            depth):

        cost = self.expected_bit_cost(depth)

        hours = max(bit_hours,1)

        return round(
            cost / hours,
            2
        )


    def mechanical_specific_energy(
            self,
            wob,
            rpm,
            rop,
            bit_size):
        """
        Simplified Mechanical Specific Energy.
        psi
        """

        area = math.pi * (bit_size / 2) ** 2

        if rop <= 0:

            return 0

        mse = (

            (wob * 1000) / area +

            (120 * rpm) / rop

        )

        return round(mse,0)


    def bit_summary(
            self,
            bit_hours,
            depth):

        return {

            "Expected Bit Life":

                self.expected_bit_life(depth),

            "Bit Wear":

                self.bit_wear(
                    bit_hours,
                    depth),

            "Efficiency":

                self.bit_efficiency(
                    bit_hours,
                    depth),

            "Adjusted ROP":

                self.adjusted_rop(
                    bit_hours,
                    depth),

            "Dull Grade":

                self.dull_grade(
                    bit_hours,
                    depth),

            "Pull Reason":

                self.pull_reason(
                    bit_hours,
                    depth),

            "Replace":

                self.bit_replacement_required(
                    bit_hours,
                    depth)

        }
    
    # ==========================================================
    # RELIABILITY & DRILLING RISK ENGINE
    # ==========================================================

    def vibration_probability(self, depth):
        """
        Probability of severe vibration.
        """

        formation = self.formation(depth)

        return round(
            formation.vibration_risk,
            2
        )


    def stick_slip_probability(self, depth):
        """
        Stick-slip probability.
        """

        formation = self.formation(depth)

        probability = (

            formation.abrasiveness * 0.45 +

            formation.drilling_difficulty / 180

        )

        return round(

            min(probability, 0.95),

            2

        )


    def whirl_probability(self, depth):
        """
        Bit whirl probability.
        """

        formation = self.formation(depth)

        probability = (

            formation.abrasiveness * 0.30 +

            formation.quartz_pct / 250

        )

        return round(

            min(probability, 0.95),

            2

        )


    def differential_sticking_probability(self, depth):

        return round(

            self.formation(depth).differential_sticking,

            2

        )


    def lost_circulation_probability(self, depth):

        return round(

            self.formation(depth).lost_circulation_risk,

            2

        )


    def washout_probability(self, depth):

        return round(

            self.formation(depth).washout_risk,

            2

        )


    def packoff_probability(self, depth):

        return round(

            self.formation(depth).packoff_risk,

            2

        )


    def bit_balling_probability(self, depth):

        return round(

            self.formation(depth).bit_balling,

            2

        )


    # ==========================================================
    # EQUIPMENT RELIABILITY
    # ==========================================================

    def mechanical_failure_probability(
            self,
            bit_hours,
            depth):
        """
        Overall mechanical failure probability.
        """

        wear = self.bit_wear(
            bit_hours,
            depth
        ) / 100

        vibration = self.vibration_probability(depth)

        difficulty = self.drilling_difficulty(depth) / 100

        probability = (

            0.40 * wear +

            0.35 * vibration +

            0.25 * difficulty

        )

        return round(

            min(probability,0.95),

            2

        )


    def expected_mechanical_failures(
            self,
            bit_hours,
            depth):
        """
        Estimated number of failures.
        """

        probability = self.mechanical_failure_probability(
            bit_hours,
            depth
        )

        if probability < 0.20:
            return 0

        elif probability < 0.45:
            return 1

        elif probability < 0.70:
            return 2

        else:
            return 3


    # ==========================================================
    # NPT ENGINE
    # ==========================================================

    def expected_npt_hours(
            self,
            bit_hours,
            depth):
        """
        Estimated Non-Productive Time.
        """

        failures = self.expected_mechanical_failures(
            bit_hours,
            depth
        )

        vibration = self.vibration_probability(depth)

        base = failures * 4

        vibration_hours = vibration * 8

        sticking = self.differential_sticking_probability(depth) * 12

        npt = (

            base +

            vibration_hours +

            sticking

        )

        return round(

            npt,

            1

        )


    def run_efficiency(
            self,
            bit_hours,
            rotating_hours,
            depth):
        """
        Operational efficiency.
        """

        npt = self.expected_npt_hours(
            bit_hours,
            depth
        )

        total = rotating_hours + npt

        if total <= 0:
            return 100

        efficiency = (

            rotating_hours /

            total

        ) * 100

        return round(

            efficiency,

            1

        )


    # ==========================================================
    # BHA SUCCESS
    # ==========================================================

    def bha_success(
            self,
            bit_hours,
            rotating_hours,
            depth):
        """
        Overall BHA Performance.
        """

        efficiency = self.run_efficiency(
            bit_hours,
            rotating_hours,
            depth
        )

        wear = self.bit_wear(
            bit_hours,
            depth
        )

        if efficiency > 95 and wear < 35:

            return "Excellent"

        elif efficiency > 88 and wear < 60:

            return "Good"

        elif efficiency > 78:

            return "Average"

        else:

            return "Poor"


    # ==========================================================
    # RISK SUMMARY
    # ==========================================================

    def risk_summary(
            self,
            bit_hours,
            rotating_hours,
            depth):

        return {

            "Mechanical Failures":

                self.expected_mechanical_failures(
                    bit_hours,
                    depth
                ),

            "NPT Hours":

                self.expected_npt_hours(
                    bit_hours,
                    depth
                ),

            "Run Efficiency":

                self.run_efficiency(
                    bit_hours,
                    rotating_hours,
                    depth
                ),

            "BHA Success":

                self.bha_success(
                    bit_hours,
                    rotating_hours,
                    depth
                ),

            "Stick Slip":

                self.stick_slip_probability(depth),

            "Whirl":

                self.whirl_probability(depth),

            "Differential Sticking":

                self.differential_sticking_probability(depth),

            "Lost Circulation":

                self.lost_circulation_probability(depth),

            "Washout":

                self.washout_probability(depth),

            "Packoff":

                self.packoff_probability(depth)

        }
    
        # ==========================================================
    # ENGINEERING INTELLIGENCE
    # ==========================================================

    def hole_section(self, depth):
        """
        Returns the expected hole section based on depth.
        """

        if depth < 500:
            return '36"'

        elif depth < 3000:
            return '26"'

        elif depth < 9000:
            return '17-1/2"'

        elif depth < 18000:
            return '12-1/4"'

        else:
            return '8-1/2"'


    def casing_section(self, depth):
        """
        Returns casing program section.
        """

        if depth < 500:
            return "Conductor"

        elif depth < 3000:
            return "Surface"

        elif depth < 9000:
            return "Intermediate"

        elif depth < 18000:
            return "Production"

        return "Production Liner"


    def is_new_formation(
            self,
            previous_depth,
            current_depth):

        previous = self.formation(previous_depth).name

        current = self.formation(current_depth).name

        return previous != current


    def drilling_complexity(self, depth):
        """
        Returns an overall drilling complexity score.
        """

        formation = self.formation(depth)

        score = (

            formation.drilling_difficulty * 0.45 +

            formation.abrasiveness * 100 * 0.20 +

            formation.vibration_risk * 100 * 0.15 +

            formation.differential_sticking * 100 * 0.10 +

            formation.lost_circulation_risk * 100 * 0.10

        )

        return round(score,1)


    def complexity_category(self, depth):

        score = self.drilling_complexity(depth)

        if score < 25:
            return "Very Easy"

        elif score < 45:
            return "Easy"

        elif score < 65:
            return "Moderate"

        elif score < 85:
            return "Difficult"

        return "Extreme"


    def recommended_bha(self, depth):
        """
        Returns complete BHA recommendation.
        """

        return {

            "Hole Section":

                self.hole_section(depth),

            "Bit":

                self.recommended_bit(depth),

            "Bit Size":

                self.recommended_bit_size(depth),

            "Motor":

                self.recommended_motor(depth),

            "RSS":

                self.use_rss(depth),

            "RPM":

                self.recommended_rpm(depth),

            "RPM Range":

                self.recommended_rpm_range(depth),

            "WOB":

                self.recommended_wob(depth),

            "WOB Range":

                self.recommended_wob_range(depth),

            "Flow Rate":

                self.recommended_flowrate(depth),

            "Flow Range":

                self.recommended_flowrate_range(depth),

            "Mud Weight":

                self.recommended_mud_weight(depth)

        }


    def engineering_report(self, depth):
        """
        Complete engineering recommendation.
        """

        formation = self.formation(depth)

        return {

            "Formation":

                formation.name,

            "Age":

                formation.age,

            "Lithology":

                formation.lithology,

            "Hole Section":

                self.hole_section(depth),

            "Casing":

                self.casing_section(depth),

            "Bit":

                self.recommended_bit(depth),

            "Bit Size":

                self.recommended_bit_size(depth),

            "Motor":

                self.recommended_motor(depth),

            "RSS":

                self.use_rss(depth),

            "Mud Weight":

                self.recommended_mud_weight(depth),

            "Pressure Window":

                self.pressure_window(depth),

            "Expected ROP":

                self.expected_rop(depth),

            "Bit Life":

                self.expected_bit_life(depth),

            "Difficulty":

                self.drilling_difficulty(depth),

            "Complexity":

                self.drilling_complexity(depth),

            "Complexity Category":

                self.complexity_category(depth),

            "Temperature":

                formation.temperature,

            "Pore Pressure":

                formation.pore_pressure,

            "Fracture Gradient":

                formation.fracture_gradient

        }


    def print_engineering_report(self, depth):
        """
        Prints a formatted engineering report.
        """

        report = self.engineering_report(depth)

        print()

        print("=" * 70)
        print("ENGINEERING REPORT")
        print("=" * 70)

        for key, value in report.items():

            print(f"{key:<28}: {value}")

        print("=" * 70)

        print()

if __name__ == "__main__":

    geo = GeologyEngine()

    test_depth = 15420

    geo.print_engineering_report(test_depth)

    print()

    print("Recommended BHA")

    print("-"*60)

    for k, v in geo.recommended_bha(test_depth).items():

        print(f"{k:<20}: {v}")

    print()

    print("Risk Summary")

    print("-"*60)

    bit_hours = 95

    rotating_hours = 95

    for k, v in geo.risk_summary(
        bit_hours,
        rotating_hours,
        test_depth
    ).items():

        print(f"{k:<25}: {v}")
    