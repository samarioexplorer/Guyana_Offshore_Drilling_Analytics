from bha.assembly import BottomHoleAssembly
from bha.engineering import BHAEngineering

bha = BottomHoleAssembly(
    name="Hydraulics Test",
    section="Vertical",
    hole_size_in=17.5,
)

bha.flow_rate_gpm = 700
bha.pump_pressure_psi = 3000
bha.bit_pressure_loss_psi = 1700
bha.nozzle_area_in2 = 0.88

eng = BHAEngineering(bha)

print("===== HYDRAULICS =====")
print(f"HHP        : {eng.hydraulic_horsepower:.2f}")
print(f"Bit HHP    : {eng.bit_hydraulic_horsepower:.2f}")
print(f"Efficiency : {eng.hydraulic_efficiency:.3f}")
print(f"Jet Vel    : {eng.jet_velocity:.2f}")
print(f"HSI        : {eng.hydraulic_horsepower_per_square_inch:.2f}")
print(f"Cleaning   : {eng.bit_cleaning_index:.2f}")
print(f"Status     : {eng.hydraulic_status}")