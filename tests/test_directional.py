from bha.assembly import BottomHoleAssembly
from bha.engineering import BHAEngineering

bha = BottomHoleAssembly(
    name="Directional Test",
    section="Build",
    hole_size_in=12.25,
)

bha.inclination_deg = 12
bha.target_inclination_deg = 20

bha.azimuth_deg = 35
bha.target_azimuth_deg = 45

bha.course_length_ft = 100

eng = BHAEngineering(bha)

print("===== DIRECTIONAL =====")
print(f"Inclination Change : {eng.inclination_change:.2f}")
print(f"Azimuth Change     : {eng.azimuth_change:.2f}")
print(f"Dogleg Angle       : {eng.dogleg_angle:.2f}")
print(f"DLS                : {eng.dogleg_severity:.2f} °/100ft")
print(f"Build Rate         : {eng.build_rate:.2f}")
print(f"Turn Rate          : {eng.turn_rate:.2f}")
print(f"Difficulty         : {eng.directional_difficulty}")
print(f"Recommendation     : {eng.directional_recommendation}")