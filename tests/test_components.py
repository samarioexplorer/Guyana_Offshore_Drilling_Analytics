from bha.components import BHAComponent
from bha.enums import ComponentType

component = BHAComponent(
    name="8in Collar",
    component_type=ComponentType.DRILL_COLLAR,
    od_in=8.0,
    id_in=2.75,
    length_ft=31,
    weight_lb=950
)

print(component)

print("SUCCESS")
