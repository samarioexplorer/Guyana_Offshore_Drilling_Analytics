"""
==========================================================
Survey Analysis Module

Engineering Suite v3.0

Survey statistics and engineering KPIs
==========================================================
"""

from __future__ import annotations

from .survey import SurveyModule


class SurveyAnalysisModule(SurveyModule):
    """
    Survey analytics.
    """

    @property
    def survey_station_count(self):

        return len(getattr(self, "_survey", []))

    @property
    def max_dls(self):

        if not hasattr(self, "_survey"):

            return 0.0

        return max(

            station.dls

            for station in self._survey

        )

    @property
    def average_dls(self):

        if not hasattr(self, "_survey"):

            return 0.0

        if len(self._survey) <= 1:

            return 0.0

        return (

            sum(

                station.dls

                for station in self._survey[1:]

            )

            /

            (len(self._survey) - 1)

        )

    @property
    def maximum_inclination(self):

        if not hasattr(self, "_survey"):

            return 0.0

        return max(

            station.inc

            for station in self._survey

        )

    @property
    def maximum_departure(self):

        if not hasattr(self, "_survey"):

            return 0.0

        return max(

            station.closure

            for station in self._survey

        )

    @property
    def final_tvd(self):

        if not hasattr(self, "_survey"):

            return 0.0

        return self._survey[-1].tvd

    @property
    def final_northing(self):

        if not hasattr(self, "_survey"):

            return 0.0

        return self._survey[-1].northing

    @property
    def final_easting(self):

        if not hasattr(self, "_survey"):

            return 0.0

        return self._survey[-1].easting

    @property
    def final_closure(self):

        if not hasattr(self, "_survey"):

            return 0.0

        return self._survey[-1].closure

    @property
    def well_type(self):

        inc = self.maximum_inclination

        if inc < 10:

            return "Vertical"

        if inc < 60:

            return "Directional"

        if inc < 85:

            return "High Angle"

        return "Horizontal"

    @property
    def survey_quality(self):

        dls = self.max_dls

        if dls < 3:

            return "Excellent"

        if dls < 6:

            return "Good"

        if dls < 10:

            return "Moderate"

        return "Aggressive"

    