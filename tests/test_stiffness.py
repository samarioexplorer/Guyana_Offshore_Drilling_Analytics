from bha.assembly import BottomHoleAssembly
from bha.engineering import BHAEngineering

bha = BottomHoleAssembly(
    name="Stiffness Test",
    section="Vertical",
    hole_size_in=12.25,
)

eng = BHAEngineering(bha)

print("===== STIFFNESS =====")
print(f"Moment of Inertia : {eng.average_moment_of_inertia:.2f}")
print(f"Polar Moment      : {eng.average_polar_moment:.2f}")
print(f"Section Modulus   : {eng.average_section_modulus:.2f}")
print(f"Flexural Rigidity : {eng.flexural_rigidity:.2f}")
print(f"Radius Gyration   : {eng.radius_of_gyration:.2f}")
print(f"Stiffness Index   : {eng.stiffness_index:.2f}")
print(f"Status            : {eng.stiffness_status}")