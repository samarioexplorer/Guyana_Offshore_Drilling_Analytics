from bha.assembly import BottomHoleAssembly
from bha.engineering import BHAEngineering
from bha.reports.report import EngineeringReport
from bha.enums import HoleSection

bha = BottomHoleAssembly(
    name="Demo BHA",
    section= "Build",
    hole_size_in=12.25,
)

eng = BHAEngineering(bha)

report = EngineeringReport(eng)

report.print()