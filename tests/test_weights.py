from bha.assembly import BottomHoleAssembly
from bha.engineering import BHAEngineering

bha = BottomHoleAssembly(
    name="Weight Test",
    section="Vertical",
    hole_size_in=17.5
)

eng = BHAEngineering(bha)

print("===== WEIGHTS =====")

print("Total Weight      :", eng.total_weight)
print("Collar Weight     :", eng.collar_weight)
print("HWDP Weight       :", eng.hwdp_weight)
print("Drill Pipe Weight :", eng.drillpipe_weight)
print("Bit Weight        :", eng.bit_weight)
print("Motor Weight      :", eng.motor_weight)
print("MWD Weight        :", eng.mwd_weight)
print("RSS Weight        :", eng.rss_weight)
print("Average lb/ft     :", eng.average_weight_per_ft)