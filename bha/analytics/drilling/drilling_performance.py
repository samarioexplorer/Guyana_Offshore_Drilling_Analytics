from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DrillingPerformance:

    footage_ft: float

    drilling_hours: float

    on_bottom_hours: float

    rotary_hours: float

    sliding_hours: float

    circulating_hours: float

    trip_hours: float

    npt_hours: float

    connection_hours: float

    @property
    def average_rop(self):

        if self.drilling_hours == 0:
            return 0.0

        return self.footage_ft / self.drilling_hours

    @property
    def mechanical_rop(self):

        if self.on_bottom_hours == 0:
            return 0.0

        return self.footage_ft / self.on_bottom_hours

    @property
    def rotary_percentage(self):

        if self.on_bottom_hours == 0:
            return 0.0

        return (
            self.rotary_hours
            / self.on_bottom_hours
            * 100
        )

    @property
    def sliding_percentage(self):

        if self.on_bottom_hours == 0:
            return 0.0

        return (
            self.sliding_hours
            / self.on_bottom_hours
            * 100
        )

    @property
    def npt_percentage(self):

        total = self.drilling_hours + self.npt_hours

        if total == 0:
            return 0.0

        return self.npt_hours / total * 100

    @property
    def connection_percentage(self):

        if self.drilling_hours == 0:
            return 0.0

        return (
            self.connection_hours
            / self.drilling_hours
            * 100
        )

    @property
    def utilization(self):

        total = (
            self.drilling_hours
            + self.trip_hours
            + self.npt_hours
        )

        if total == 0:
            return 0.0

        return (
            self.drilling_hours
            / total
            * 100
        )

    @property
    def summary(self):

        return {

            "Average ROP (ft/hr)": round(self.average_rop, 2),

            "Mechanical ROP": round(self.mechanical_rop, 2),

            "Rotary %": round(self.rotary_percentage, 1),

            "Sliding %": round(self.sliding_percentage, 1),

            "Connection %": round(self.connection_percentage, 1),

            "NPT %": round(self.npt_percentage, 1),

            "Rig Utilization %": round(self.utilization, 1),

        }

    