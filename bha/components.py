"""
========================================================================
BHA Engineering Suite v2.0

components.py

Engineering component models.

Author : Anibal Ceballos
========================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .enums import (
    ComponentType,
    SteelGrade,
    ConnectionType,
    BitType,
    BearingType,
)

@dataclass(slots=True)
class BHAComponent:
    """
    Base class for every BHA component.
    """

    name: str

    component_type: ComponentType

    outer_diameter_in: float

    inner_diameter_in: float

    length_ft: float

    weight_lb: float

    connection: ConnectionType

    manufacturer: str = "Generic"

    model: str = ""

    serial_number: str = ""

    description: str = ""

    def __post_init__(self):

        if self.outer_diameter_in <= 0:
            raise ValueError("Outer diameter must be positive.")

        if self.length_ft <= 0:
            raise ValueError("Length must be positive.")

        if self.weight_lb < 0:
            raise ValueError("Weight cannot be negative.")
        
    @property
    def weight_per_ft(self) -> float:
        return self.weight_lb / self.length_ft

    @property
    def is_rotating(self) -> bool:
        return True

    def summary(self) -> str:
        return (
            f"{self.component_type.value}: "
            f"{self.name} "
            f"({self.length_ft:.1f} ft)"
        )
    
    @property
    def od(self) -> float:
        return self.outer_diameter_in


    @property
    def id(self) -> float:
        return self.inner_diameter_in
    
    @property
    def diameter_in(self) -> float:
        return self.outer_diameter_in
    
@dataclass(slots=True)
class Bit(BHAComponent):

    bit_type: BitType = BitType.PDC

    blade_count: int = 6

    nozzle_count: int = 7

    iadc: str = ""

    bearing: BearingType = BearingType.NONE

    cutter_size_mm: float = 16.0

    def __post_init__(self):

        super().__post_init__()

        self.component_type = ComponentType.BIT

@dataclass(slots=True)
class DrillCollar(BHAComponent):

    steel_grade: SteelGrade = SteelGrade.S135

    spiral: bool = False

    def __post_init__(self):

        super().__post_init__()

        self.component_type = ComponentType.DRILL_COLLAR

@dataclass(slots=True)
class HWDP(BHAComponent):

    steel_grade: SteelGrade = SteelGrade.S135

    center_upset: bool = True

    def __post_init__(self):

        super().__post_init__()

        self.component_type = ComponentType.HWDP

@dataclass(slots=True)
class DrillPipe(BHAComponent):

    steel_grade: SteelGrade = SteelGrade.S135

    tool_joint_od: float = 6.625

    def __post_init__(self):

        super().__post_init__()

        self.component_type = ComponentType.DRILL_PIPE

@dataclass(slots=True)
class Stabilizer(BHAComponent):

    blade_count: int = 3

    gauge_length_ft: float = 2.5

    replaceable_blades: bool = False

    def __post_init__(self):

        super().__post_init__()

        self.component_type = ComponentType.STABILIZER

@dataclass(slots=True)
class MudMotor(BHAComponent):

    stages: float = 7.0

    lobe_ratio: str = "7/8"

    bend_deg: float = 1.5

    max_flow_rate_gpm: int = 700

    max_torque_ftlb: int = 12000

    def __post_init__(self):

        super().__post_init__()

        self.component_type = ComponentType.MUD_MOTOR

@dataclass(slots=True)
class RSS(BHAComponent):

    steering_mode: str = "Push-the-Bit"

    max_build_rate_deg100ft: float = 12.0

    def __post_init__(self):

        super().__post_init__()

        self.component_type = ComponentType.RSS

@dataclass(slots=True)
class MWD(BHAComponent):

    gamma: bool = True

    inclination: bool = True

    azimuth: bool = True

    shock_sensor: bool = True

    vibration_sensor: bool = True

    def __post_init__(self):

        super().__post_init__()

        self.component_type = ComponentType.MWD

@dataclass(slots=True)
class LWD(BHAComponent):

    resistivity: bool = True

    density: bool = False

    neutron: bool = False

    sonic: bool = False

    caliper: bool = False

    def __post_init__(self):

        super().__post_init__()

        self.component_type = ComponentType.LWD

@dataclass(slots=True)
class Jar(BHAComponent):

    hydraulic: bool = True

    firing_load_lb: float = 60000

    def __post_init__(self):

        super().__post_init__()

        self.component_type = ComponentType.JAR

@dataclass(slots=True)
class ShockSub(BHAComponent):

    travel_in: float = 2.5

    spring_rate: float = 30000

    def __post_init__(self):

        super().__post_init__()

        self.component_type = ComponentType.SHOCK_SUB

@dataclass(slots=True)
class FloatSub(BHAComponent):

    valve_type: str = "Flapper"

    pressure_rating_psi: int = 15000

    def __post_init__(self):

        super().__post_init__()

        self.component_type = ComponentType.FLOAT_SUB



    