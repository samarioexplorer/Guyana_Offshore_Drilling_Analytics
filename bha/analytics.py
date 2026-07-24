"""
===========================================================================
BHA ENGINEERING SUITE
Version 2.0

Engineering Analytics
===========================================================================

Advanced engineering calculations used for optimization,
Power BI dashboards and drilling KPIs.
"""

from __future__ import annotations

from dataclasses import dataclass

from .assembly import BottomHoleAssembly
from .components import BHAComponent
from .enums import ComponentType


# ===========================================================================
# RESULTS
# ===========================================================================

@dataclass(slots=True)
class BHAAnalysis:

    total_length_ft: float
    total_weight_lb: float

    collar_length_ft: float
    collar_weight_lb: float

    hwdp_length_ft: float
    hwdp_weight_lb: float

    tool_length_ft: float
    tool_weight_lb: float

    average_component_weight: float

    stiffness_index: float

    wob_available: float

    recommended_wob: float

    neutral_point_ft: float

    buckling_risk: str

    engineering_score: float


# ===========================================================================
# ENGINEERING
# ===========================================================================

class EngineeringAnalytics:

    """
    Performs complete engineering analysis.
    """

    # ------------------------------------------------------------------

    @staticmethod
    def total_length(bha: BottomHoleAssembly) -> float:

        return sum(c.length_ft for c in bha.components)

    # ------------------------------------------------------------------

    @staticmethod
    def total_weight(bha: BottomHoleAssembly) -> float:

        return sum(c.weight_lb for c in bha.components)

    # ------------------------------------------------------------------

    @staticmethod
    def collar_components(
        bha: BottomHoleAssembly
    ) -> list[BHAComponent]:

        return [

            c

            for c in bha.components

            if c.component_type == ComponentType.DRILL_COLLAR

        ]

    # ------------------------------------------------------------------

    @staticmethod
    def hwdp_components(
        bha: BottomHoleAssembly
    ) -> list[BHAComponent]:

        return [

            c

            for c in bha.components

            if c.component_type == ComponentType.HWDP

        ]

    # ------------------------------------------------------------------

    @staticmethod
    def tool_components(
        bha: BottomHoleAssembly
    ) -> list[BHAComponent]:

        return [

            c

            for c in bha.components

            if c.component_type not in {

                ComponentType.DRILL_COLLAR,

                ComponentType.HWDP,

                ComponentType.DRILL_PIPE,

            }

        ]

    # ------------------------------------------------------------------

    @staticmethod
    def collar_length(
        bha: BottomHoleAssembly
    ) -> float:

        return sum(

            c.length_ft

            for c in EngineeringAnalytics.collar_components(bha)

        )

    # ------------------------------------------------------------------

    @staticmethod
    def collar_weight(
        bha: BottomHoleAssembly
    ) -> float:

        return sum(

            c.weight_lb

            for c in EngineeringAnalytics.collar_components(bha)

        )

    # ------------------------------------------------------------------

    @staticmethod
    def hwdp_length(
        bha: BottomHoleAssembly
    ) -> float:

        return sum(

            c.length_ft

            for c in EngineeringAnalytics.hwdp_components(bha)

        )

    # ------------------------------------------------------------------

    @staticmethod
    def hwdp_weight(
        bha: BottomHoleAssembly
    ) -> float:

        return sum(

            c.weight_lb

            for c in EngineeringAnalytics.hwdp_components(bha)

        )

    # ------------------------------------------------------------------

    @staticmethod
    def tool_length(
        bha: BottomHoleAssembly
    ) -> float:

        return sum(

            c.length_ft

            for c in EngineeringAnalytics.tool_components(bha)

        )

    # ------------------------------------------------------------------

    @staticmethod
    def tool_weight(
        bha: BottomHoleAssembly
    ) -> float:

        return sum(

            c.weight_lb

            for c in EngineeringAnalytics.tool_components(bha)

        )

    # ------------------------------------------------------------------

    @staticmethod
    def stiffness_index(
        bha: BottomHoleAssembly
    ) -> float:

        collars = EngineeringAnalytics.collar_weight(bha)

        total = EngineeringAnalytics.total_weight(bha)

        if total == 0:

            return 0

        return collars / total

    # ------------------------------------------------------------------

    @staticmethod
    def wob_available(
        bha: BottomHoleAssembly
    ) -> float:

        return EngineeringAnalytics.collar_weight(bha) * 0.85

    # ------------------------------------------------------------------

    @staticmethod
    def recommended_wob(
        bha: BottomHoleAssembly
    ) -> float:

        return EngineeringAnalytics.wob_available(bha) * 0.75

    # ------------------------------------------------------------------

    @staticmethod
    def neutral_point(
        bha: BottomHoleAssembly
    ) -> float:

        collars = EngineeringAnalytics.collar_length(bha)

        return collars * 0.55

    # ------------------------------------------------------------------

    @staticmethod
    def buckling_risk(
        bha: BottomHoleAssembly
    ) -> str:

        stiffness = EngineeringAnalytics.stiffness_index(bha)

        if stiffness > 0.70:

            return "LOW"

        if stiffness > 0.50:

            return "MEDIUM"

        return "HIGH"

    # ------------------------------------------------------------------

    @staticmethod
    def engineering_score(
        bha: BottomHoleAssembly
    ) -> float:

        score = 100.0

        stiffness = EngineeringAnalytics.stiffness_index(bha)

        if stiffness < 0.45:

            score -= 25

        elif stiffness < 0.60:

            score -= 10

        if EngineeringAnalytics.buckling_risk(bha) == "HIGH":

            score -= 20

        return max(score, 0)

    # ------------------------------------------------------------------

    @classmethod
    def analyze(
        cls,
        bha: BottomHoleAssembly,
    ) -> BHAAnalysis:

        total_length = cls.total_length(bha)
        total_weight = cls.total_weight(bha)

        return BHAAnalysis(

            total_length_ft=total_length,

            total_weight_lb=total_weight,

            collar_length_ft=cls.collar_length(bha),

            collar_weight_lb=cls.collar_weight(bha),

            hwdp_length_ft=cls.hwdp_length(bha),

            hwdp_weight_lb=cls.hwdp_weight(bha),

            tool_length_ft=cls.tool_length(bha),

            tool_weight_lb=cls.tool_weight(bha),

            average_component_weight=(
                total_weight / len(bha.components)
                if bha.components else 0
            ),

            stiffness_index=cls.stiffness_index(bha),

            wob_available=cls.wob_available(bha),

            recommended_wob=cls.recommended_wob(bha),

            neutral_point_ft=cls.neutral_point(bha),

            buckling_risk=cls.buckling_risk(bha),

            engineering_score=cls.engineering_score(bha),

        )