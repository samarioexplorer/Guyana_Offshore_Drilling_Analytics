"""
==========================================================
Directional Module

Engineering Suite v3.0

Directional drilling calculations.
==========================================================
"""

from __future__ import annotations

from math import radians, degrees, acos, sin, cos

from .vibrations import VibrationsModule


class DirectionalModule(VibrationsModule):
    """
    Directional drilling calculations.
    """

    @property
    def inclination_change(self):

        return (

            self.bha.target_inclination_deg

            -

            self.bha.inclination_deg

        )

    @property
    def azimuth_change(self):

        return (

            self.bha.target_azimuth_deg

            -

            self.bha.azimuth_deg

        )

    @property
    def dogleg_angle(self):

        inc1 = radians(self.bha.inclination_deg)
        inc2 = radians(self.bha.target_inclination_deg)

        azi1 = radians(self.bha.azimuth_deg)
        azi2 = radians(self.bha.target_azimuth_deg)

        value = (

            cos(inc1)

            *

            cos(inc2)

            +

            sin(inc1)

            *

            sin(inc2)

            *

            cos(azi2 - azi1)

        )

        value = max(-1.0, min(1.0, value))

        return degrees(acos(value))

    @property
    def dogleg_severity(self):

        interval = self.delta_md

        if interval == 0:
            return 0.0

        return (

            self.dogleg_angle

            * 100

            / interval

        )

    @property
    def build_rate(self):

        if self.bha.course_length_ft == 0:

            return 0.0

        return (

            self.inclination_change

            *

            100

            /

            self.bha.course_length_ft

        )

    @property
    def turn_rate(self):

        if self.bha.course_length_ft == 0:

            return 0.0

        return (

            self.azimuth_change

            *

            100

            /

            self.bha.course_length_ft

        )

    @property
    def directional_difficulty(self):

        dls = self.dogleg_severity

        if dls < 2:

            return "Easy"

        if dls < 5:

            return "Moderate"

        if dls < 8:

            return "Difficult"

        return "Extreme"

    @property
    def directional_recommendation(self):

        difficulty = self.directional_difficulty

        if difficulty == "Easy":

            return "Conventional BHA suitable."

        if difficulty == "Moderate":

            return "Motor or RSS recommended."

        if difficulty == "Difficult":

            return "Packed-hole BHA with RSS."

        return "High-performance RSS required."

    