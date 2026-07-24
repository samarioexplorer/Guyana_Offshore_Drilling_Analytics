"""
==========================================================
Stiffness Module

Engineering Suite v3.0

Mechanical stiffness calculations.
==========================================================
"""

from __future__ import annotations

from math import pi

from .torque_drag import TorqueDragModule

from ..constants import (
    STEEL_YOUNGS_MODULUS_PSI,
)


class StiffnessModule(TorqueDragModule):
    """
    Mechanical stiffness calculations.
    """

    @property
    def moment_of_inertia(self):

        if self.component_count == 0:

            return 0.0

        od = self.average_outer_diameter

        id = self.average_inner_diameter

        return (

            pi

            /

            64

        ) * (

            od**4

            -

            id**4

        )
    
    @property
    def polar_moment(self):

        return 2 * self.moment_of_inertia
    
    @property
    def section_modulus(self):

        if self.average_outer_diameter == 0:

            return 0.0

        return (

            self.moment_of_inertia

            /

            (

                self.average_outer_diameter

                /

                2

            )

        )
    
    @property
    def cross_section_area(self):

        od = self.average_outer_diameter

        id = self.average_inner_diameter

        return (

            pi

            /

            4

        ) * (

            od**2

            -

            id**2

        )
    
    @property
    def radius_of_gyration(self):

        if self.cross_section_area == 0:

            return 0.0

        return (

            self.moment_of_inertia

            /

            self.cross_section_area

        ) ** 0.5
    

    @property
    def flexural_rigidity(self):

        return (

            STEEL_YOUNGS_MODULUS_PSI

            *

            self.moment_of_inertia

        )
    
    @property
    def average_stiffness(self):

        if self.total_length == 0:

            return 0.0

        return (

            self.flexural_rigidity

            /

            self.total_length

        )
    
    @property
    def stiffness_index(self):

        if self.total_weight == 0:

            return 0.0

        return (

            self.flexural_rigidity

            /

            self.total_weight

        )
    
    @property
    def stiffness_status(self):

        index = self.stiffness_index

        if index < 500:

            return "Flexible"

        if index < 1500:

            return "Balanced"

        return "Rigid"
    
    @property
    def stiffness_recommendation(self):

        status = self.stiffness_status

        if status == "Flexible":

            return "Increase drill collar section."

        if status == "Balanced":

            return "Suitable for most applications."

        return "High build capability."
    
###############################################################################
# BACKWARD-COMPATIBILITY ALIASES
###############################################################################

    @property
    def average_moment_of_inertia(self):
        return self.moment_of_inertia


    @property
    def average_polar_moment(self):
        return self.polar_moment


    @property
    def average_section_modulus(self):
        return self.section_modulus


    @property
    def average_flexural_rigidity(self):
        return self.flexural_rigidity