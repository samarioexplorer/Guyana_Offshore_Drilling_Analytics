"""
==========================================================
Torque & Drag Module

Engineering Suite v3.0

Soft-string torque & drag calculations.
==========================================================
"""

from __future__ import annotations

from .buckling import BucklingModule

from ..constants import (
    DEFAULT_OPEN_HOLE_FRICTION,
)


class TorqueDragModule(BucklingModule):
    """
    Torque & Drag calculations.

    Phase 1:
        • Effective Weight
        • Drag Force
        • Hookload
        • Pickup
        • Slackoff
        • Rotary Torque
    """

    @property
    def effective_weight(self):

        return (

            self.total_weight

            * self.bha.buoyancy_factor

        )
    
    @property
    def normal_force(self):

        return self.effective_weight 
    
    @property
    def drag_force(self):

        return (

            self.bha.open_hole_friction

            * self.normal_force

        )
    
    @property
    def surface_hookload(self):

        return (

            self.effective_weight

            + self.drag_force

        )
    
    @property
    def pickup_hookload(self):

        return (

            self.effective_weight

            + self.drag_force

        )
    
    @property
    def slackoff_hookload(self):

        return (

            self.effective_weight

            - self.drag_force

        )
    
    @property
    def rotary_torque(self):

        radius = (

            self.average_outer_diameter

            / 2

        ) / 12

        return (

            self.drag_force

            * radius

        )
    
    @property
    def torque_drag_status(self):

        if self.drag_force < 5000:

            return "Low"

        if self.drag_force < 15000:

            return "Moderate"

        if self.drag_force < 30000:

            return "High"



    @property
    def torque_drag_recommendation(self):

        status = self.torque_drag_status

        if status == "Low":

            return "Normal drilling."

        if status == "Moderate":

            return "Monitor hookload."

        if status == "High":

            return "Reduce friction or WOB."

        return "Review BHA design immediately."

    @property
    def hookload(self):
        return self.surface_hookload


    @property
    def pickup_load(self):
        return self.pickup_hookload


    @property
    def slackoff_load(self):
        return self.slackoff_hookload
    
    