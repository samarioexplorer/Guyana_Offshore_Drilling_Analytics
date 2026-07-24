"""
Torque & Drag reporting.
"""

from .torque_drag import TorqueDragResult


class TorqueDragReport:

    @staticmethod
    def print(result: TorqueDragResult):

        print()

        print("=" * 70)

        print("TORQUE & DRAG ANALYSIS")

        print("=" * 70)

        print(f"String Weight (lb)      : {result.string_weight:,.0f}")

        print(f"Buoyed Weight (lb)      : {result.buoyed_weight:,.0f}")

        print(f"Pickup Weight (lb)      : {result.pickup_weight:,.0f}")

        print(f"Slack-Off Weight (lb)   : {result.slackoff_weight:,.0f}")

        print(f"Rotating Weight (lb)    : {result.rotating_weight:,.0f}")

        print(f"Drag Force (lb)         : {result.drag_force:,.0f}")

        print(f"Surface Torque (ft-lb)  : {result.surface_torque:,.0f}")

        print(f"Efficiency              : {result.efficiency:.2%}")

        print("=" * 70)

        