"""
==========================================================
Engineering Suite v3.0

Public Engineering API
==========================================================
"""

from .well_summary import WellSummaryModule


class BHAEngineering(WellSummaryModule):
    """
    Main engineering interface.
    """

    def __init__(self, bha):

        super().__init__(bha)

    @property
    def report(self):
        from bha.reports.report import EngineeringReport
        return EngineeringReport(self)