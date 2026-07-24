from bha.assembly import BottomHoleAssembly
from bha.engineering import BHAEngineering

bha = BottomHoleAssembly(
    name="Trajectory Test",
    section="Build",
    hole_size_in=12.25,
)

bha.md1_ft = 0
bha.md2_ft = 100

bha.inclination_deg = 12
bha.target_inclination_deg = 20

bha.azimuth_deg = 35
bha.target_azimuth_deg = 45

eng = BHAEngineering(bha)

print("===== TRAJECTORY =====")
print(f"ΔMD       : {eng.delta_md:.2f}")
print(f"ΔNorth    : {eng.delta_north:.2f}")
print(f"ΔEast     : {eng.delta_east:.2f}")
print(f"ΔTVD      : {eng.delta_tvd:.2f}")
print(f"Northing  : {eng.northing:.2f}")
print(f"Easting   : {eng.easting:.2f}")
print(f"TVD       : {eng.tvd:.2f}")
print(f"Closure   : {eng.closure_distance:.2f}")
print(f"Azimuth   : {eng.closure_azimuth:.2f}")