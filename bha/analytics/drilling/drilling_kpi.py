"""
==========================================================
Drilling KPI Engine

Engineering Suite v4.2
==========================================================
"""

from __future__ import annotations

from dataclasses import dataclass

from .drilling_performance import DrillingPerformance


@dataclass(slots=True)
class DrillingKPI:

    performance: DrillingPerformance

    @property
    def score(self):

        score = 100

        # NPT
        if self.performance.npt_percentage > 15:
            score -= 20
        elif self.performance.npt_percentage > 10:
            score -= 10
        elif self.performance.npt_percentage > 5:
            score -= 5

        # Rig utilization
        if self.performance.utilization < 70:
            score -= 20
        elif self.performance.utilization < 80:
            score -= 10
        elif self.performance.utilization < 90:
            score -= 5

        # Sliding percentage
        if self.performance.sliding_percentage > 50:
            score -= 10
        elif self.performance.sliding_percentage > 35:
            score -= 5

        # Connection time
        if self.performance.connection_percentage > 15:
            score -= 10
        elif self.performance.connection_percentage > 10:
            score -= 5

        return max(score, 0)

    @property
    def rating(self):

        s = self.score

        if s >= 95:
            return "Outstanding"

        if s >= 90:
            return "Excellent"

        if s >= 80:
            return "Good"

        if s >= 70:
            return "Fair"

        return "Needs Improvement"

    @property
    def recommendations(self):

        rec = []

        if self.performance.npt_percentage > 10:
            rec.append("Reduce Non-Productive Time (NPT).")

        if self.performance.connection_percentage > 10:
            rec.append("Improve connection efficiency.")

        if self.performance.sliding_percentage > 40:
            rec.append("Reduce sliding drilling where possible.")

        if self.performance.utilization < 85:
            rec.append("Increase rig utilization.")

        if not rec:
            rec.append("Excellent drilling performance.")

        return rec

    @property
    def summary(self):

        return {

            "Average ROP": round(self.performance.average_rop,2),

            "Mechanical ROP": round(self.performance.mechanical_rop,2),

            "Rotary %": round(self.performance.rotary_percentage,1),

            "Sliding %": round(self.performance.sliding_percentage,1),

            "Connection %": round(self.performance.connection_percentage,1),

            "NPT %": round(self.performance.npt_percentage,1),

            "Rig Utilization %": round(self.performance.utilization,1),

            "Performance Score": self.score,

            "Rating": self.rating,

            "Recommendations": self.recommendations,

        }

    