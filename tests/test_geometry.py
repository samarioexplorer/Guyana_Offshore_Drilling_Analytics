from bha.assembly import BottomHoleAssembly
from bha.engineering import BHAEngineering

bha = BottomHoleAssembly(
    name="Geometry Test",
    section="Vertical",
    hole_size_in=17.5
)

eng = BHAEngineering(bha)

print("===== GEOMETRY =====")
print("Components :", eng.component_count)
print("Length (ft):", eng.total_length)
print("Average OD :", eng.average_od)
print("Average ID :", eng.average_id)