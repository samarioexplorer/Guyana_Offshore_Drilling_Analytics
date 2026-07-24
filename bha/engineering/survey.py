"""
==========================================================
Survey Module

Engineering Suite v3.0

Directional Survey Processing
==========================================================
"""

from __future__ import annotations

from dataclasses import dataclass

from .trajectory import TrajectoryModule


@dataclass
class SurveyStation:

    md: float

    inc: float

    azi: float

    tvd: float = 0.0

    northing: float = 0.0

    easting: float = 0.0

    closure: float = 0.0

    closure_azimuth: float = 0.0

    dls: float = 0.0


class SurveyModule(TrajectoryModule):

    """
    Survey calculations.
    """

    def process_survey(
    self,
    stations: list[SurveyStation],
) -> list[SurveyStation]:

        if len(stations) < 2:
            return stations

        stations[0].tvd = 0
        stations[0].northing = 0
        stations[0].easting = 0
        stations[0].closure = 0
        stations[0].closure_azimuth = 0
        stations[0].dls = 0

        for i in range(1, len(stations)):

            prev = stations[i-1]

            cur = stations[i]

            self.bha.md1_ft = prev.md
            self.bha.md2_ft = cur.md

            self.bha.inclination_deg = prev.inc
            self.bha.target_inclination_deg = cur.inc

            self.bha.azimuth_deg = prev.azi
            self.bha.target_azimuth_deg = cur.azi

            self.bha.tvd1_ft = prev.tvd
            self.bha.northing1_ft = prev.northing
            self.bha.easting1_ft = prev.easting

            self.clear_cache()

            cur.tvd = self.tvd

            cur.northing = self.northing

            cur.easting = self.easting

            cur.closure = self.closure_distance

            cur.closure_azimuth = self.closure_azimuth

            cur.dls = self.dogleg_severity

        self._survey = stations

        return stations

        