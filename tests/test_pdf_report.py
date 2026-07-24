from bha.assembly import BottomHoleAssembly
from bha.engineering import BHAEngineering
from bha.enums import HoleSection

bha = BottomHoleAssembly(
    name="Demo BHA",
    section=HoleSection.SURFACE,
    hole_size_in=12.25,
)

eng = BHAEngineering(bha)

eng.report.to_pdf("output/BHA_Report.pdf")

print("PDF report created successfully.")