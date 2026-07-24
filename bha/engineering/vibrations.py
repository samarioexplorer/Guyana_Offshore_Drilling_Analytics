"""
==========================================================
Vibrations Module

Engineering Suite v3.0

BHA vibration assessment.

==========================================================
"""

from __future__ import annotations

from .stiffness import StiffnessModule


class VibrationsModule(StiffnessModule):
    """
    Vibration calculations.

    Phase 1:
        • Axial vibration
        • Lateral vibration
        • Torsional vibration
        • Stick-slip
        • Bit whirl
        • Resonance index
    """

    @property
    def axial_vibration_index(self):

        if self.total_weight == 0:
            return 0.0

        return self.available_wob / self.total_weight
    
    @property
    def lateral_vibration_index(self):

        if self.flexural_rigidity == 0:
            return 0.0

        return self.rotary_torque / self.flexural_rigidity
    
    @property
    def torsional_vibration_index(self):

        if self.rotary_torque == 0:
            return 0.0

        return self.drag_force / self.rotary_torque
    
    @property
    def stick_slip_index(self):

        return (

            self.torsional_vibration_index

            *

            self.wob_utilization

        )
    
    @property
    def bit_whirl_index(self):

        if self.average_outer_diameter == 0:
            return 0.0

        return (

            self.lateral_vibration_index

            *

            self.average_outer_diameter

        )
    
    @property
    def resonance_index(self):

        if self.stiffness_index == 0:
            return 0.0

        return (

            self.rotary_torque

            /

            self.stiffness_index

        )
    
    @property
    def vibration_severity(self):

        score = max(

            self.axial_vibration_index,

            self.lateral_vibration_index,

            self.torsional_vibration_index,

        )

        if score < 0.30:
            return "Low"

        if score < 0.60:
            return "Moderate"

        if score < 1.00:
            return "High"

        return "Critical"
    
    @property
    def vibration_recommendation(self):

        severity = self.vibration_severity

        if severity == "Low":
            return "Normal drilling."

        if severity == "Moderate":
            return "Monitor RPM and WOB."

        if severity == "High":
            return "Reduce RPM or WOB."

        return "Immediate corrective action required."

    @property
    def axial_vibration(self):
        return self.axial_vibration_index


    @property
    def lateral_vibration(self):
        return self.lateral_vibration_index


    @property
    def torsional_vibration(self):
        return self.torsional_vibration_index
    
    
 
