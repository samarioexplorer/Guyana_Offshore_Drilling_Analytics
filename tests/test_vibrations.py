from bha.assembly import BottomHoleAssembly
from bha.engineering import BHAEngineering

bha = BottomHoleAssembly(
    name="Vibration Test",
    section="Vertical",
    hole_size_in=12.25,
)

eng = BHAEngineering(bha)

print("===== VIBRATIONS =====")
print(f"Axial       : {eng.axial_vibration_index:.3f}")
print(f"Lateral     : {eng.lateral_vibration_index:.3f}")
print(f"Torsional   : {eng.torsional_vibration_index:.3f}")
print(f"Stick-Slip  : {eng.stick_slip_index:.3f}")
print(f"Bit Whirl   : {eng.bit_whirl_index:.3f}")
print(f"Resonance   : {eng.resonance_index:.3f}")
print(f"Severity    : {eng.vibration_severity}")
print(f"Advice      : {eng.vibration_recommendation}")