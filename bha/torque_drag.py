"""
===========================================================================
TORQUE & DRAG ENGINE
===========================================================================

Simplified torque and drag calculations.

This module estimates:

• Hookload
• Pickup Weight
• Slack-Off Weight
• Rotary Torque
• Friction Loss
• Mechanical Efficiency

Version 2.0
"""

from __future__ import annotations

from dataclasses import dataclass

from .assembly import BottomHoleAssembly
from .analytics import EngineeringAnalytics


# ============================================================================
# WELL SECTION
# ============================================================================

@dataclass(slots=True)
class WellSection:

    md_ft: float

    inclination_deg: float

    azimuth_deg: float

    friction_factor: float = 0.25


# ============================================================================
# RESULTS
# ============================================================================

@dataclass(slots=True)
class TorqueDragResult:

    string_weight: float

    buoyed_weight: float

    pickup_weight: float

    slackoff_weight: float

    rotating_weight: float

    surface_torque: float

    drag_force: float

    efficiency: float


# ============================================================================
# TORQUE & DRAG ENGINE
# ============================================================================

class TorqueDragEngine:

    """
    Simplified torque & drag calculations.

    Assumptions:

    • Soft string
    • Constant friction
    • Average inclination
    """

    BUOYANCY_FACTOR = 0.87

    # ------------------------------------------------------------------

    @staticmethod
    def string_weight(bha: BottomHoleAssembly) -> float:

        return EngineeringAnalytics.total_weight(bha)

    # ------------------------------------------------------------------

    @classmethod
    def buoyed_weight(cls, bha):

        return cls.string_weight(bha) * cls.BUOYANCY_FACTOR

    # ------------------------------------------------------------------

    @classmethod
    def drag_force(cls, bha, section: WellSection):

        weight = cls.buoyed_weight(bha)

        return (

            weight
            * section.friction_factor
            * (section.inclination_deg / 90)

        )

    # ------------------------------------------------------------------

    @classmethod
    def pickup_weight(cls, bha, section):

        return (

            cls.buoyed_weight(bha)

            + cls.drag_force(bha, section)

        )

    # ------------------------------------------------------------------

    @classmethod
    def slackoff_weight(cls, bha, section):

        return (

            cls.buoyed_weight(bha)

            - cls.drag_force(bha, section)

        )

    # ------------------------------------------------------------------

    @classmethod
    def rotating_weight(cls, bha):

        return cls.buoyed_weight(bha)

    # ------------------------------------------------------------------

    @classmethod
    def surface_torque(cls, bha, section):

        drag = cls.drag_force(bha, section)

        radius_ft = bha.hole_size / 24

        return drag * radius_ft

    # ------------------------------------------------------------------

    @classmethod
    def efficiency(cls, bha, section):

        pickup = cls.pickup_weight(bha, section)

        slack = cls.slackoff_weight(bha, section)

        return slack / pickup

    # ------------------------------------------------------------------

    @classmethod
    def analyze(

        cls,

        bha: BottomHoleAssembly,

        section: WellSection,

    ) -> TorqueDragResult:

        return TorqueDragResult(

            string_weight=cls.string_weight(bha),

            buoyed_weight=cls.buoyed_weight(bha),

            pickup_weight=cls.pickup_weight(bha, section),

            slackoff_weight=cls.slackoff_weight(bha, section),

            rotating_weight=cls.rotating_weight(bha),

            surface_torque=cls.surface_torque(bha, section),

            drag_force=cls.drag_force(bha, section),

            efficiency=cls.efficiency(bha, section),

        )
    
    