from bha.assembly import BottomHoleAssembly
from bha.engineering import BHAEngineering
from bha.enums import HoleSection

bha = BottomHoleAssembly(
    name="Demo BHA",
    section=HoleSection.PRODUCTION,
    hole_size_in=12.25,
)

eng = BHAEngineering(bha)

eng.report.to_excel("reports/bha_report.xlsx")

print("Excel report created successfully.")