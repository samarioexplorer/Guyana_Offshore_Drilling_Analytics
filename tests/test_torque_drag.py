from bha.assembly import BottomHoleAssembly
from bha.engineering import BHAEngineering

bha = BottomHoleAssembly(
    name="Torque Test",
    section="Vertical",
    hole_size_in=12.25,
)

eng = BHAEngineering(bha)

print("===== TORQUE & DRAG =====")
print(f"Effective Weight : {eng.effective_weight:.2f} lb")
print(f"Drag Force       : {eng.drag_force:.2f} lb")
print(f"Hookload         : {eng.surface_hookload:.2f} lb")
print(f"Pickup           : {eng.pickup_hookload:.2f} lb")
print(f"Slackoff         : {eng.slackoff_hookload:.2f} lb")
print(f"Rotary Torque    : {eng.rotary_torque:.2f} ft-lb")
print(f"Status           : {eng.torque_drag_status}")
print(f"Recommendation   : {eng.torque_drag_recommendation}")