from bha.assembly import BottomHoleAssembly
from bha.engineering import BHAEngineering

bha = BottomHoleAssembly(
    name="Buckling Test",
    section="Vertical",
    hole_size_in=17.5,
)

eng = BHAEngineering(bha)

print("===== BUCKLING =====")
print(f"Neutral Point        : {eng.neutral_point:.2f} ft")
print(f"Collar Length        : {eng.collar_length:.2f} ft")
print(f"Buckling Ratio       : {eng.buckling_ratio:.2f}")
print(f"Critical Load        : {eng.critical_buckling_load:.2f} lb")
print(f"Safety Factor        : {eng.buckling_safety_factor:.2f}")
print(f"Status               : {eng.buckling_status}")
print(f"Recommendation       : {eng.buckling_recommendation}")

