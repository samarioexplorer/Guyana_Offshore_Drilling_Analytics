"""
==========================================================
Trajectory Module

Engineering Suite v3.0

Minimum Curvature Survey Calculations
==========================================================
"""

from __future__ import annotations

from math import (
    sin,
    cos,
    tan,
    radians,
    degrees,
    atan2,
)
from .directional import DirectionalModule


class TrajectoryModule(DirectionalModule):
    """
    Minimum Curvature calculations.
    """

    @property
    def delta_md(self):

        return self.bha.md2_ft - self.bha.md1_ft

    @property
    def ratio_factor(self):

        dl = radians(self.dogleg_angle)

        if abs(dl) < 1e-9:
            return 1.0

        return (2 / dl) * tan(dl / 2)

    @property
    def delta_north(self):

        inc1 = radians(self.bha.inclination_deg)
        inc2 = radians(self.bha.target_inclination_deg)

        azi1 = radians(self.bha.azimuth_deg)
        azi2 = radians(self.bha.target_azimuth_deg)

        return (

            self.delta_md

            / 2

            *

            (

                sin(inc1) * cos(azi1)

                +

                sin(inc2) * cos(azi2)

            )

            *

            self.ratio_factor

        )

    @property
    def delta_east(self):

        inc1 = radians(self.bha.inclination_deg)
        inc2 = radians(self.bha.target_inclination_deg)

        azi1 = radians(self.bha.azimuth_deg)
        azi2 = radians(self.bha.target_azimuth_deg)

        return (

            self.delta_md

            / 2

            *

            (

                sin(inc1) * sin(azi1)

                +

                sin(inc2) * sin(azi2)

            )

            *

            self.ratio_factor

        )

    @property
    def delta_tvd(self):

        inc1 = radians(self.bha.inclination_deg)
        inc2 = radians(self.bha.target_inclination_deg)

        return (

            self.delta_md

            / 2

            *

            (

                cos(inc1)

                +

                cos(inc2)

            )

            *

            self.ratio_factor

        )

    @property
    def northing(self):

        return self.bha.northing1_ft + self.delta_north


    @property
    def easting(self):

        return self.bha.easting1_ft + self.delta_east


    @property
    def tvd(self):

        return self.bha.tvd1_ft + self.delta_tvd

    @property
    def closure_distance(self):

        return (

            self.northing**2

            +

            self.easting**2

        ) ** 0.5

    from math import atan2, degrees

    @property
    def closure_azimuth(self):

        if self.closure_distance == 0:
            return 0.0

        az = degrees(

            atan2(

                self.easting,

                self.northing,

            )

        )

        return az % 360

    