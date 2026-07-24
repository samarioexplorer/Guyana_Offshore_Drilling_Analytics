from bha.assembly import BottomHoleAssembly
from bha.engineering import BHAEngineering

bha = BottomHoleAssembly(
    name="WOB Test",
    section="Vertical",
    hole_size_in=17.5
)

eng = BHAEngineering(bha)

print("===== WOB =====")

print("Available WOB :", eng.available_wob)
print("Recommended   :", eng.recommended_wob)
print("Reserve       :", eng.wob_reserve)
print("Reserve %     :", eng.wob_reserve_percent)
print("Utilization   :", eng.wob_utilization)
print("Neutral Point :", eng.neutral_point)
print("Safety Factor :", eng.wob_safety_factor)
print("Status        :", eng.wob_status)