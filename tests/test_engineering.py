from bha.assembly import BottomHoleAssembly
from bha.engineering import BHAEngineering

bha = BottomHoleAssembly(
    name="Test BHA",
    section="Vertical",
    hole_size_in=17.5
)

eng = BHAEngineering(bha)

print("Components      :", eng.number_of_components)
print("Length (ft)     :", eng.total_length)
print("Weight (lb)     :", eng.total_weight)

print()

print("Available WOB   :", eng.available_wob)
print("Recommended WOB :", eng.recommended_wob)
print("Utilization     :", eng.wob_utilization)
print("Reserve (%)     :", eng.wob_reserve_percent)
print("Neutral Point   :", eng.neutral_point)
print("Status          :", eng.wob_status)

bha.flow_rate_gpm = 650

bha.pump_pressure_psi = 3200

bha.bit_pressure_loss_psi = 1800

bha.nozzle_area_in2 = 0.82

print()
print("===== HYDRAULICS =====")

print("HHP       :", round(eng.hydraulic_horsepower, 2))

print("Bit HHP   :", round(eng.bit_hydraulic_horsepower, 2))

print("Efficiency:", round(eng.hydraulic_efficiency, 3))

print("Jet Vel   :", round(eng.jet_velocity, 2))

print("HSI       :", round(eng.hydraulic_hsi, 2))

print("Cleaning  :", round(eng.cleaning_index, 3))

print("Status    :", eng.hydraulics_status)

print()
print("===== BUCKLING =====")

print("Critical Sinusoidal :", round(eng.critical_sinusoidal_load, 1))

print("Critical Helical    :", round(eng.critical_helical_load, 1))

print("Compression Ratio   :", round(eng.compression_ratio, 2))

print("Safety Factor       :", round(eng.buckling_safety_factor, 2))

print("Status              :", eng.buckling_status)

print("Recommendation      :", eng.buckling_recommendation)

