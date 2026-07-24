"""
======================================================================
GEOLOGY DATABASE
Guyana Offshore Drilling Analytics

Version : 3.1

Author : Anibal Ceballos

======================================================================

DESCRIPTION

This module contains the geological database used by the drilling
simulator.

Each formation stores its geological and rock mechanics properties.

This module DOES NOT perform calculations.

Engineering calculations belong in:

    geology.py

======================================================================
"""

from dataclasses import dataclass
from typing import List


# ============================================================
# CONSTANTS
# ============================================================

GRAVITY = 32.174                  # ft/s²

GEOTHERMAL_GRADIENT = 1.45        # °F /100 ft

SEAWATER_DENSITY = 8.6            # ppg

MAX_RESERVOIR_TEMP = 275          # °F

DEFAULT_SURFACE_TEMP = 78         # °F


# ============================================================
# FORMATION CLASS
# ============================================================

@dataclass
class Formation:
    """
    Geological Formation

    Stores geological, petrophysical and drilling properties.

    No calculations are performed here.
    """

    # --------------------------------------------------------
    # BASIC INFORMATION
    # --------------------------------------------------------

    name: str

    age: str

    depositional_environment: str

    lithology: str

    color: str


    # --------------------------------------------------------
    # DEPTH
    # --------------------------------------------------------

    top_depth: float

    base_depth: float


    # --------------------------------------------------------
    # ROCK MECHANICS
    # --------------------------------------------------------

    ucs: float                     # psi

    tensile_strength: float        # psi

    abrasiveness: float            # 0-1

    young_modulus: float           # Mpsi

    poisson_ratio: float


    # --------------------------------------------------------
    # MINERALOGY
    # --------------------------------------------------------

    quartz_pct: float

    clay_pct: float

    calcite_pct: float

    dolomite_pct: float


    # --------------------------------------------------------
    # PETROPHYSICS
    # --------------------------------------------------------

    porosity: float                # fraction

    permeability: float            # mD

    water_saturation: float


    # --------------------------------------------------------
    # PRESSURE
    # --------------------------------------------------------

    pore_pressure: float           # ppg equivalent

    fracture_gradient: float       # ppg equivalent


    # --------------------------------------------------------
    # TEMPERATURE
    # --------------------------------------------------------

    temperature: float             # °F


    # --------------------------------------------------------
    # DRILLING PERFORMANCE
    # --------------------------------------------------------

    expected_rop: float            # ft/hr

    drilling_difficulty: float     # 0-100


    # --------------------------------------------------------
    # RECOMMENDED DRILLING SYSTEM
    # --------------------------------------------------------

    recommended_bit: str

    recommended_bit_size: float

    recommended_motor: str

    recommended_rss: bool


    # --------------------------------------------------------
    # DRILLING PARAMETERS
    # --------------------------------------------------------

    recommended_rpm_min: int

    recommended_rpm_max: int

    recommended_wob_min: int

    recommended_wob_max: int

    recommended_flowrate_min: int

    recommended_flowrate_max: int


    # --------------------------------------------------------
    # MUD PROGRAM
    # --------------------------------------------------------

    mud_weight_min: float

    mud_weight_max: float

    recommended_mud_type: str


    # --------------------------------------------------------
    # HAZARDS
    # --------------------------------------------------------

    differential_sticking: float

    bit_balling: float

    vibration_risk: float

    washout_risk: float

    lost_circulation_risk: float

    packoff_risk: float


    # --------------------------------------------------------
    # ECONOMICS
    # --------------------------------------------------------

    average_bit_life_hr: float

    average_cost_per_foot: float

    # ============================================================
# GEOLOGICAL DATABASE
# OFFSHORE GUYANA BASIN
# PART 1 - SHALLOW SECTION
# ============================================================

FORMATIONS: List[Formation] = [

    # ========================================================
    # MARINE WATER
    # ========================================================

    Formation(

        name="Marine Water",

        age="Present",

        depositional_environment="Ocean",

        lithology="Sea Water",

        color="Blue",

        top_depth=0,

        base_depth=6500,

        ucs=0,

        tensile_strength=0,

        abrasiveness=0.00,

        young_modulus=0,

        poisson_ratio=0.50,

        quartz_pct=0,

        clay_pct=0,

        calcite_pct=0,

        dolomite_pct=0,

        porosity=1.00,

        permeability=100000,

        water_saturation=1.00,

        pore_pressure=8.60,

        fracture_gradient=0.00,

        temperature=78,

        expected_rop=0,

        drilling_difficulty=0,

        recommended_bit="None",

        recommended_bit_size=0,

        recommended_motor="None",

        recommended_rss=False,

        recommended_rpm_min=0,

        recommended_rpm_max=0,

        recommended_wob_min=0,

        recommended_wob_max=0,

        recommended_flowrate_min=0,

        recommended_flowrate_max=0,

        mud_weight_min=8.60,

        mud_weight_max=8.60,

        recommended_mud_type="Sea Water",

        differential_sticking=0,

        bit_balling=0,

        vibration_risk=0,

        washout_risk=0,

        lost_circulation_risk=0,

        packoff_risk=0,

        average_bit_life_hr=0,

        average_cost_per_foot=0

    ),

    # ========================================================
    # SEABED SEDIMENTS
    # ========================================================

    Formation(

        name="Seabed Sediments",

        age="Holocene",

        depositional_environment="Deep Marine",

        lithology="Very Soft Clay",

        color="Dark Gray",

        top_depth=6500,

        base_depth=6900,

        ucs=250,

        tensile_strength=25,

        abrasiveness=0.05,

        young_modulus=0.20,

        poisson_ratio=0.47,

        quartz_pct=8,

        clay_pct=82,

        calcite_pct=8,

        dolomite_pct=2,

        porosity=0.62,

        permeability=4500,

        water_saturation=1.00,

        pore_pressure=8.65,

        fracture_gradient=9.10,

        temperature=82,

        expected_rop=320,

        drilling_difficulty=4,

        recommended_bit="PDC",

        recommended_bit_size=36.0,

        recommended_motor="Conventional",

        recommended_rss=False,

        recommended_rpm_min=40,

        recommended_rpm_max=70,

        recommended_wob_min=10,

        recommended_wob_max=25,

        recommended_flowrate_min=900,

        recommended_flowrate_max=1200,

        mud_weight_min=8.6,

        mud_weight_max=8.8,

        recommended_mud_type="Seawater Gel",

        differential_sticking=0.02,

        bit_balling=0.30,

        vibration_risk=0.05,

        washout_risk=0.03,

        lost_circulation_risk=0.01,

        packoff_risk=0.08,

        average_bit_life_hr=350,

        average_cost_per_foot=45

    ),

    # ========================================================
    # GEORGETOWN FORMATION
    # ========================================================

    Formation(

        name="Georgetown Formation",

        age="Pleistocene",

        depositional_environment="Shelf Marine",

        lithology="Claystone / Sand",

        color="Gray",

        top_depth=6900,

        base_depth=8500,

        ucs=1800,

        tensile_strength=180,

        abrasiveness=0.18,

        young_modulus=0.90,

        poisson_ratio=0.36,

        quartz_pct=28,

        clay_pct=60,

        calcite_pct=8,

        dolomite_pct=4,

        porosity=0.42,

        permeability=1400,

        water_saturation=1.00,

        pore_pressure=9.1,

        fracture_gradient=10.8,

        temperature=95,

        expected_rop=220,

        drilling_difficulty=15,

        recommended_bit="PDC",

        recommended_bit_size=26.0,

        recommended_motor="Conventional",

        recommended_rss=False,

        recommended_rpm_min=60,

        recommended_rpm_max=90,

        recommended_wob_min=20,

        recommended_wob_max=35,

        recommended_flowrate_min=850,

        recommended_flowrate_max=1100,

        mud_weight_min=9.2,

        mud_weight_max=9.8,

        recommended_mud_type="KCl Polymer",

        differential_sticking=0.05,

        bit_balling=0.20,

        vibration_risk=0.08,

        washout_risk=0.05,

        lost_circulation_risk=0.03,

        packoff_risk=0.08,

        average_bit_life_hr=260,

        average_cost_per_foot=72

    ),

    # ========================================================
    # UPPER SAND SEQUENCE
    # ========================================================

    Formation(

        name="Upper Sand Sequence",

        age="Miocene",

        depositional_environment="Deltaic",

        lithology="Fine Sandstone",

        color="Light Brown",

        top_depth=8500,

        base_depth=10500,

        ucs=5200,

        tensile_strength=450,

        abrasiveness=0.35,

        young_modulus=2.60,

        poisson_ratio=0.28,

        quartz_pct=65,

        clay_pct=20,

        calcite_pct=10,

        dolomite_pct=5,

        porosity=0.32,

        permeability=900,

        water_saturation=0.95,

        pore_pressure=10.8,

        fracture_gradient=12.6,

        temperature=118,

        expected_rop=155,

        drilling_difficulty=32,

        recommended_bit="PDC",

        recommended_bit_size=17.5,

        recommended_motor="High Performance",

        recommended_rss=True,

        recommended_rpm_min=90,

        recommended_rpm_max=140,

        recommended_wob_min=25,

        recommended_wob_max=45,

        recommended_flowrate_min=700,

        recommended_flowrate_max=950,

        mud_weight_min=10.8,

        mud_weight_max=11.5,

        recommended_mud_type="KCl Polymer",

        differential_sticking=0.10,

        bit_balling=0.08,

        vibration_risk=0.12,

        washout_risk=0.06,

        lost_circulation_risk=0.05,

        packoff_risk=0.06,

        average_bit_life_hr=220,

        average_cost_per_foot=115

 ),

    # ========================================================
    # NEW AMSTERDAM FORMATION
    # ========================================================

    Formation(

        name="New Amsterdam Formation",

        age="Upper Miocene",

        depositional_environment="Deep Marine Shale",

        lithology="Shale",

        color="Dark Gray",

        top_depth=10500,

        base_depth=12500,

        ucs=8200,

        tensile_strength=720,

        abrasiveness=0.45,

        young_modulus=4.20,

        poisson_ratio=0.30,

        quartz_pct=35,

        clay_pct=55,

        calcite_pct=8,

        dolomite_pct=2,

        porosity=0.26,

        permeability=45,

        water_saturation=0.98,

        pore_pressure=11.8,

        fracture_gradient=13.9,

        temperature=145,

        expected_rop=95,

        drilling_difficulty=48,

        recommended_bit="Hybrid",

        recommended_bit_size=12.25,

        recommended_motor="High Performance",

        recommended_rss=True,

        recommended_rpm_min=100,

        recommended_rpm_max=160,

        recommended_wob_min=25,

        recommended_wob_max=40,

        recommended_flowrate_min=550,

        recommended_flowrate_max=800,

        mud_weight_min=11.8,

        mud_weight_max=12.8,

        recommended_mud_type="Synthetic Oil Base Mud",

        differential_sticking=0.18,

        bit_balling=0.12,

        vibration_risk=0.20,

        washout_risk=0.10,

        lost_circulation_risk=0.06,

        packoff_risk=0.12,

        average_bit_life_hr=180,

        average_cost_per_foot=170

    ),

    # ========================================================
    # CANJE FORMATION
    # ========================================================

    Formation(

        name="Canje Formation",

        age="Upper Cretaceous",

        depositional_environment="Marine Shale",

        lithology="Interbedded Shale",

        color="Black",

        top_depth=12500,

        base_depth=14500,

        ucs=10500,

        tensile_strength=950,

        abrasiveness=0.62,

        young_modulus=5.80,

        poisson_ratio=0.28,

        quartz_pct=42,

        clay_pct=45,

        calcite_pct=10,

        dolomite_pct=3,

        porosity=0.20,

        permeability=8,

        water_saturation=0.92,

        pore_pressure=13.2,

        fracture_gradient=15.6,

        temperature=175,

        expected_rop=72,

        drilling_difficulty=66,

        recommended_bit="Hybrid",

        recommended_bit_size=12.25,

        recommended_motor="High Performance",

        recommended_rss=True,

        recommended_rpm_min=110,

        recommended_rpm_max=170,

        recommended_wob_min=30,

        recommended_wob_max=45,

        recommended_flowrate_min=500,

        recommended_flowrate_max=700,

        mud_weight_min=13.0,

        mud_weight_max=14.0,

        recommended_mud_type="Synthetic Oil Base Mud",

        differential_sticking=0.25,

        bit_balling=0.08,

        vibration_risk=0.30,

        washout_risk=0.12,

        lost_circulation_risk=0.10,

        packoff_risk=0.15,

        average_bit_life_hr=150,

        average_cost_per_foot=220

    ),

    # ========================================================
    # UPPER CAMPANIAN SHALE
    # ========================================================

    Formation(

        name="Upper Campanian Shale",

        age="Campanian",

        depositional_environment="Marine",

        lithology="Hard Shale",

        color="Dark Brown",

        top_depth=14500,

        base_depth=17000,

        ucs=13800,

        tensile_strength=1200,

        abrasiveness=0.78,

        young_modulus=7.10,

        poisson_ratio=0.26,

        quartz_pct=50,

        clay_pct=38,

        calcite_pct=10,

        dolomite_pct=2,

        porosity=0.17,

        permeability=3,

        water_saturation=0.85,

        pore_pressure=14.5,

        fracture_gradient=16.9,

        temperature=205,

        expected_rop=52,

        drilling_difficulty=82,

        recommended_bit="PDC",

        recommended_bit_size=8.5,

        recommended_motor="Mud Motor",

        recommended_rss=True,

        recommended_rpm_min=120,

        recommended_rpm_max=190,

        recommended_wob_min=18,

        recommended_wob_max=32,

        recommended_flowrate_min=350,

        recommended_flowrate_max=550,

        mud_weight_min=14.3,

        mud_weight_max=15.2,

        recommended_mud_type="Premium Synthetic OBM",

        differential_sticking=0.32,

        bit_balling=0.04,

        vibration_risk=0.42,

        washout_risk=0.16,

        lost_circulation_risk=0.12,

        packoff_risk=0.18,

        average_bit_life_hr=120,

        average_cost_per_foot=285

    ),

    # ========================================================
    # MAASTRICHTIAN SAND
    # ========================================================

    Formation(

        name="Maastrichtian Sand",

        age="Maastrichtian",

        depositional_environment="Deepwater Turbidite",

        lithology="Sandstone",

        color="Light Gray",

        top_depth=17000,

        base_depth=19000,

        ucs=6800,

        tensile_strength=620,

        abrasiveness=0.52,

        young_modulus=4.80,

        poisson_ratio=0.24,

        quartz_pct=72,

        clay_pct=12,

        calcite_pct=12,

        dolomite_pct=4,

        porosity=0.27,

        permeability=950,

        water_saturation=0.38,

        pore_pressure=15.2,

        fracture_gradient=17.6,

        temperature=225,

        expected_rop=82,

        drilling_difficulty=58,

        recommended_bit="PDC",

        recommended_bit_size=8.5,

        recommended_motor="Mud Motor",

        recommended_rss=True,

        recommended_rpm_min=140,

        recommended_rpm_max=220,

        recommended_wob_min=15,

        recommended_wob_max=28,

        recommended_flowrate_min=320,

        recommended_flowrate_max=480,

        mud_weight_min=15.0,

        mud_weight_max=15.8,

        recommended_mud_type="Premium Synthetic OBM",

        differential_sticking=0.14,

        bit_balling=0.03,

        vibration_risk=0.24,

        washout_risk=0.08,

        lost_circulation_risk=0.08,

        packoff_risk=0.08,

        average_bit_life_hr=165,

        average_cost_per_foot=245

    ),

        # ========================================================
    # CAMPANIAN RESERVOIR
    # ========================================================

    Formation(

        name="Campanian Reservoir",

        age="Campanian",

        depositional_environment="Deepwater Turbidite",

        lithology="High Quality Sandstone",

        color="Light Brown",

        top_depth=19000,

        base_depth=21500,

        ucs=7200,

        tensile_strength=650,

        abrasiveness=0.48,

        young_modulus=5.10,

        poisson_ratio=0.24,

        quartz_pct=76,

        clay_pct=8,

        calcite_pct=12,

        dolomite_pct=4,

        porosity=0.29,

        permeability=2200,

        water_saturation=0.22,

        pore_pressure=15.8,

        fracture_gradient=18.3,

        temperature=245,

        expected_rop=78,

        drilling_difficulty=56,

        recommended_bit="PDC",

        recommended_bit_size=8.5,

        recommended_motor="Mud Motor",

        recommended_rss=True,

        recommended_rpm_min=150,

        recommended_rpm_max=220,

        recommended_wob_min=18,

        recommended_wob_max=30,

        recommended_flowrate_min=320,

        recommended_flowrate_max=500,

        mud_weight_min=15.5,

        mud_weight_max=16.2,

        recommended_mud_type="Premium Synthetic OBM",

        differential_sticking=0.10,

        bit_balling=0.02,

        vibration_risk=0.18,

        washout_risk=0.05,

        lost_circulation_risk=0.05,

        packoff_risk=0.04,

        average_bit_life_hr=180,

        average_cost_per_foot=235

    ),

    # ========================================================
    # TURONIAN SOURCE ROCK
    # ========================================================

    Formation(

        name="Turonian Source Rock",

        age="Turonian",

        depositional_environment="Marine Source Rock",

        lithology="Organic Rich Shale",

        color="Black",

        top_depth=21500,

        base_depth=23500,

        ucs=16800,

        tensile_strength=1450,

        abrasiveness=0.82,

        young_modulus=8.20,

        poisson_ratio=0.25,

        quartz_pct=55,

        clay_pct=32,

        calcite_pct=10,

        dolomite_pct=3,

        porosity=0.11,

        permeability=0.01,

        water_saturation=0.18,

        pore_pressure=16.4,

        fracture_gradient=18.8,

        temperature=265,

        expected_rop=34,

        drilling_difficulty=94,

        recommended_bit="Roller Cone",

        recommended_bit_size=8.5,

        recommended_motor="Mud Motor",

        recommended_rss=True,

        recommended_rpm_min=80,

        recommended_rpm_max=140,

        recommended_wob_min=30,

        recommended_wob_max=45,

        recommended_flowrate_min=280,

        recommended_flowrate_max=420,

        mud_weight_min=16.2,

        mud_weight_max=17.0,

        recommended_mud_type="Premium Synthetic OBM",

        differential_sticking=0.38,

        bit_balling=0.01,

        vibration_risk=0.52,

        washout_risk=0.22,

        lost_circulation_risk=0.12,

        packoff_risk=0.20,

        average_bit_life_hr=95,

        average_cost_per_foot=355

    ),

    # ========================================================
    # BASEMENT
    # ========================================================

    Formation(

        name="Crystalline Basement",

        age="Precambrian",

        depositional_environment="Basement",

        lithology="Granite",

        color="Pink",

        top_depth=23500,

        base_depth=30000,

        ucs=32000,

        tensile_strength=3000,

        abrasiveness=1.00,

        young_modulus=12.5,

        poisson_ratio=0.20,

        quartz_pct=92,

        clay_pct=0,

        calcite_pct=4,

        dolomite_pct=4,

        porosity=0.01,

        permeability=0,

        water_saturation=0,

        pore_pressure=16.8,

        fracture_gradient=19.4,

        temperature=280,

        expected_rop=12,

        drilling_difficulty=100,

        recommended_bit="Roller Cone",

        recommended_bit_size=8.5,

        recommended_motor="Mud Motor",

        recommended_rss=False,

        recommended_rpm_min=60,

        recommended_rpm_max=120,

        recommended_wob_min=40,

        recommended_wob_max=60,

        recommended_flowrate_min=250,

        recommended_flowrate_max=380,

        mud_weight_min=16.5,

        mud_weight_max=17.2,

        recommended_mud_type="Premium Synthetic OBM",

        differential_sticking=0.12,

        bit_balling=0,

        vibration_risk=0.75,

        washout_risk=0.30,

        lost_circulation_risk=0.05,

        packoff_risk=0.02,

        average_bit_life_hr=60,

        average_cost_per_foot=520

    )

]

# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def get_formation(depth: float) -> Formation:
    """
    Returns the formation corresponding to the supplied depth.
    """

    for formation in FORMATIONS:

        if formation.top_depth <= depth < formation.base_depth:

            return formation

    return FORMATIONS[-1]


def get_all_formations() -> List[Formation]:
    """
    Returns the complete formation list.
    """

    return FORMATIONS


def total_formations():

    return len(FORMATIONS)


def formation_names():

    return [f.name for f in FORMATIONS]


def validate_database():

    """
    Checks for depth gaps between formations.
    """

    for i in range(len(FORMATIONS)-1):

        current = FORMATIONS[i]

        nxt = FORMATIONS[i+1]

        if current.base_depth != nxt.top_depth:

            raise ValueError(

                f"Gap detected between "

                f"{current.name} "

                f"and "

                f"{nxt.name}"

            )

    return True


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("="*70)

    print("GUYANA GEOLOGY DATABASE")

    print("="*70)

    print()

    print(f"Number of formations : {total_formations()}")

    print()

    for formation in FORMATIONS:

        print(

            f"{formation.top_depth:>6.0f} - "

            f"{formation.base_depth:<6.0f} ft   "

            f"{formation.name}"

        )

    print()

    validate_database()

    print("Database validation successful.")

    print()

    test_depth = 18750

    formation = get_formation(test_depth)

    print(f"Depth : {test_depth} ft")

    print(f"Formation : {formation.name}")

    print(f"Lithology : {formation.lithology}")

    print(f"Expected ROP : {formation.expected_rop} ft/hr")

    print(f"Recommended Bit : {formation.recommended_bit}")

    print(f"Mud Weight : {formation.mud_weight_min}-{formation.mud_weight_max} ppg")

    print("="*70)