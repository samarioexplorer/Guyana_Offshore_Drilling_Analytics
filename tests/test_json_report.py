from bha.assembly import BottomHoleAssembly
from bha.engineering import BHAEngineering
from bha.enums import HoleSection

bha = BottomHoleAssembly(
    name="Demo BHA",
    section=HoleSection.PRODUCTION,
    hole_size_in=12.25,
)

eng = BHAEngineering(bha)

eng.report.to_json("bha_report.json")

print("JSON report created successfully.")