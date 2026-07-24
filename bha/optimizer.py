"""
===========================================================================
BHA ENGINEERING SUITE

Automatic BHA Optimizer
===========================================================================

Automatically builds the optimum Bottom Hole Assembly
using engineering rules.
"""

from __future__ import annotations

from dataclasses import dataclass

from .analytics import EngineeringAnalytics
from .assembly import BottomHoleAssembly
from .components import BHAComponent
from .enums import (
    ComponentType,
    TrajectoryType,
)
from .library import ComponentLibrary


# ============================================================================
# DESIGN REQUEST
# ============================================================================

@dataclass(slots=True)
class DesignRequest:

    hole_size: float

    trajectory: TrajectoryType

    target_wob: float

    minimum_stiffness: float = 0.60

    use_rss: bool = False

    use_lwd: bool = True

    use_mwd: bool = True


# ============================================================================
# DESIGN RESULT
# ============================================================================

@dataclass(slots=True)
class DesignResult:

    bha: BottomHoleAssembly

    score: float

    available_wob: float

    stiffness: float

    warnings: list[str]


# ============================================================================
# OPTIMIZER
# ============================================================================

class BHAOptimizer:

    """
    Automatic BHA designer.
    """

    def __init__(self, library: ComponentLibrary):

        self.library = library

    # ------------------------------------------------------------------

    def design(
        self,
        request: DesignRequest,
    ) -> DesignResult:

        bha = BottomHoleAssembly(

            name=f"{request.hole_size:.2f}in Optimized BHA",

            trajectory=request.trajectory,

            hole_size=request.hole_size,

        )

        warnings = []

        # --------------------------------------------------------------
        # BIT
        # --------------------------------------------------------------

        bit = self.library.best_bit(request.hole_size)

        if bit:

            bha.add_component(bit)

        # --------------------------------------------------------------
        # RSS / MOTOR
        # --------------------------------------------------------------

        if request.use_rss:

            rss = self.library.best_rss(request.hole_size)

            if rss:

                bha.add_component(rss)

        else:

            motor = self.library.best_motor(request.hole_size)

            if motor:

                bha.add_component(motor)

        # --------------------------------------------------------------
        # MWD
        # --------------------------------------------------------------

        if request.use_mwd:

            mwd = self.library.best_mwd()

            if mwd:

                bha.add_component(mwd)

        # --------------------------------------------------------------
        # LWD
        # --------------------------------------------------------------

        if request.use_lwd:

            lwd = self.library.best_lwd()

            if lwd:

                bha.add_component(lwd)

        # --------------------------------------------------------------
        # COLLARS
        # --------------------------------------------------------------

        collars = sorted(

            self.library.by_type(ComponentType.DRILL_COLLAR),

            key=lambda x: x.weight_lb,

            reverse=True,

        )

        current_wob = 0

        for collar in collars:

            bha.add_component(collar)

            current_wob = EngineeringAnalytics.wob_available(bha)

            if current_wob >= request.target_wob:

                break

        # --------------------------------------------------------------
        # HWDP
        # --------------------------------------------------------------

        hwdps = self.library.by_type(ComponentType.HWDP)

        for pipe in hwdps[:12]:

            bha.add_component(pipe)

        # --------------------------------------------------------------
        # ENGINEERING
        # --------------------------------------------------------------

        analysis = EngineeringAnalytics.analyze(bha)

        if analysis.stiffness_index < request.minimum_stiffness:

            warnings.append(

                "Low stiffness ratio."

            )

        if analysis.wob_available < request.target_wob:

            warnings.append(

                "Target WOB not achieved."

            )

        if analysis.buckling_risk == "HIGH":

            warnings.append(

                "High buckling risk."

            )

        return DesignResult(

            bha=bha,

            score=analysis.engineering_score,

            available_wob=analysis.wob_available,

            stiffness=analysis.stiffness_index,

            warnings=warnings,

        )