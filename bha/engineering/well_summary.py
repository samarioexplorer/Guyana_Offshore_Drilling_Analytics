"""
==========================================================
Well Summary Module

Engineering Suite v3.0

Central engineering report object.
==========================================================
"""

from __future__ import annotations

from .survey_analysis import SurveyAnalysisModule


class WellSummaryModule(SurveyAnalysisModule):
    """
    Aggregates all engineering calculations into
    one report dictionary.
    """

    @property
    def geometry_summary(self):

        return {

            "Components": self.component_count,

            "Length (ft)": round(self.total_length,2),

            "Average OD (in)": round(self.average_outer_diameter,2),

            "Average ID (in)": round(self.average_inner_diameter,2),

        }

    @property
    def weight_summary(self):

        return {

            "Total Weight": round(self.total_weight,2),

            "Collars": round(self.collar_weight,2),

            "HWDP": round(self.hwdp_weight,2),

            "Drill Pipe": round(self.drillpipe_weight,2),

            "Average lb/ft": round(self.average_weight_per_ft,2),

        }

    @property
    def wob_summary(self):

        return {

            "Available": round(self.available_wob,2),

            "Recommended": round(self.recommended_wob,2),

            "Reserve": round(self.wob_reserve,2),

            "Reserve %": round(self.wob_reserve_percent,2),

            "Status": self.wob_status,

        }

    @property
    def hydraulics_summary(self):

        return {

            "HHP": round(self.hydraulic_horsepower,2),

            "Bit HHP": round(self.bit_hydraulic_horsepower,2),

            "Efficiency": round(self.hydraulic_efficiency,3),

            "Jet Velocity": round(self.jet_velocity,2),

            "HSI": round(self.hydraulic_horsepower_per_square_inch,2),

            "Cleaning": round(self.bit_cleaning_index,2),

            "Status": self.hydraulic_status,

        }

    @property
    def buckling_summary(self):

        return {

            "Neutral Point": round(self.neutral_point,2),

            "Critical Load": round(self.critical_buckling_load,2),

            "Safety Factor": round(self.buckling_safety_factor,2),

            "Status": self.buckling_status,

        }

    @property
    def torque_drag_summary(self):

        return {

            "Hookload": round(self.hookload,2),

            "Pickup": round(self.pickup_load,2),

            "Slackoff": round(self.slackoff_load,2),

            "Torque": round(self.rotary_torque,2),

            "Status": self.torque_drag_status,

        }

    @property
    def stiffness_summary(self):

        return {

            "Moment of Inertia": round(self.moment_of_inertia,2),

            "Flexural Rigidity": round(self.flexural_rigidity,2),

            "Index": round(self.stiffness_index,2),

            "Status": self.stiffness_status,

        }

    @property
    def vibration_summary(self):

        return {

            "Axial": round(self.axial_vibration,3),

            "Lateral": round(self.lateral_vibration,3),

            "Torsional": round(self.torsional_vibration,3),

            "Severity": self.vibration_severity,

        }

    @property
    def directional_summary(self):

        return {

            "Maximum Inclination": round(self.maximum_inclination, 2),

            "Maximum DLS": round(self.max_dls, 2),

            "Average DLS": round(self.average_dls, 2),

            "Well Type": self.well_type,

            "Difficulty": self.survey_quality,

        }

    @property
    def survey_summary(self):

        return {

            "Stations": self.survey_station_count,

            "Final TVD": round(self.final_tvd,2),

            "Northing": round(self.final_northing,2),

            "Easting": round(self.final_easting,2),

            "Closure": round(self.final_closure,2),

            "Maximum DLS": round(self.max_dls,2),

            "Average DLS": round(self.average_dls,2),

            "Maximum Inclination": round(self.maximum_inclination,2),

            "Well Type": self.well_type,

            "Survey Quality": self.survey_quality,

        }

    @property
    def summary(self):

        return {

            "Geometry": self.geometry_summary,

            "Weights": self.weight_summary,

            "WOB": self.wob_summary,

            "Hydraulics": self.hydraulics_summary,

            "Buckling": self.buckling_summary,

            "Torque & Drag": self.torque_drag_summary,

            "Stiffness": self.stiffness_summary,

            "Vibrations": self.vibration_summary,

            "Directional": self.directional_summary,

            "Survey": self.survey_summary,

        }

    