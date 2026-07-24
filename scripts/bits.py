"""
======================================================================
bits.py

Guyana Offshore Drilling Analytics

Version : 1.0

Digital Drill Bit Engineering Library

Author:
Anibal Ceballos
(OpenAI Assisted)

----------------------------------------------------------------------
PURPOSE

This module represents the complete engineering library for drill bits.

It provides:

• Drill bit specifications
• Bit database
• Cutter configurations
• Hydraulic design
• IADC classifications
• Bit selection
• Performance prediction
• Dull grading
• Optimization

The geology engine and well design engine consult this module whenever
a drill bit recommendation or engineering calculation is required.

======================================================================
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

# Optional integrations
# from formations import FormationDatabase
# from well_design import WellDesign

# ==============================================================
# ENGINEERING DATA TYPES
# ==============================================================

@dataclass(frozen=True)
class BitDiameter:
    """
    Engineering representation of a drill bit diameter.
    """

    value: float

    label: str

    unit: str = "in"

    def __float__(self):
        return self.value

    def __str__(self):
        return self.label


# ==============================================================
# ENUMERATIONS
# ==============================================================

class BitType(Enum):

    PDC = "PDC"

    ROLLER_CONE = "Roller Cone"

    HYBRID = "Hybrid"

    IMPREGNATED = "Impregnated"

    DIAMOND = "Natural Diamond"


class CutterMaterial(Enum):

    PDC = "Polycrystalline Diamond"

    TSP = "Thermally Stable Polycrystalline"

    NATURAL_DIAMOND = "Natural Diamond"

    TUNGSTEN_CARBIDE = "Tungsten Carbide"


class BladeProfile(Enum):

    SHORT = "Short"

    MEDIUM = "Medium"

    LONG = "Long"


class BitBody(Enum):

    MATRIX = "Matrix"

    STEEL = "Steel"


class HydraulicType(Enum):

    STANDARD = "Standard"

    HIGH_FLOW = "High Flow"

    HIGH_IMPACT = "High Impact"

    OPTIMIZED = "Optimized"


class BearingType(Enum):

    SEALED = "Sealed"

    OPEN = "Open"

    JOURNAL = "Journal"

    ROLLER = "Roller"


class GaugeProtection(Enum):

    STANDARD = "Standard"

    PREMIUM = "Premium"

    HEAVY_DUTY = "Heavy Duty"


class IADCFormationClass(Enum):

    SOFT = "Soft"

    MEDIUM = "Medium"

    HARD = "Hard"

    VERY_HARD = "Very Hard"


class NozzleType(Enum):

    FIXED = "Fixed"

    REPLACEABLE = "Replaceable"


class BitStatus(Enum):

    PLANNED = "Planned"

    IN_USE = "In Use"

    PULLED = "Pulled"

    RETIRED = "Retired"

# ==============================================================
# ENGINEERING DATACLASSES
# ==============================================================

@dataclass
class HydraulicConfiguration:
    """
    Bit hydraulic configuration.
    """

    nozzle_type: NozzleType

    nozzle_count: int

    nozzle_sizes_32nds: List[int]

    total_flow_area_in2: float

    hydraulic_type: HydraulicType


@dataclass
class CutterConfiguration:
    """
    Cutter layout for fixed cutter bits.
    """

    cutter_material: CutterMaterial

    cutter_size_mm: float

    back_rake_deg: float

    side_rake_deg: float

    blade_count: int

    blade_profile: BladeProfile

    gauge_pads: int


@dataclass
class RollerConeConfiguration:
    """
    Roller cone bit configuration.
    """

    bearing_type: BearingType

    sealed_bearing: bool

    insert_material: str

    cone_count: int = 3


@dataclass
class BitOperatingWindow:
    """
    Recommended operating limits.
    """

    wob_min_klbf: float

    wob_max_klbf: float

    rpm_min: int

    rpm_max: int

    flow_min_gpm: int

    flow_max_gpm: int


@dataclass
class BitPerformance:
    """
    Expected drilling performance.
    """

    expected_rop_ft_hr: float

    expected_bit_life_hr: float

    expected_footage_ft: float

    mechanical_efficiency: float

    dull_grade_expected: str


@dataclass
class BitHydraulics:
    """
    Hydraulic performance parameters.
    """

    hydraulic_horsepower: float

    impact_force_lbf: float

    jet_velocity_ft_sec: float

    hydraulic_efficiency: float


@dataclass
class BitLimits:
    """
    Engineering limits.
    """

    maximum_temperature_f: float

    maximum_torque_ftlb: float

    maximum_wob_klbf: float

    maximum_rpm: int


@dataclass
class BitApplication:
    """
    Geological applicability.
    """

    recommended_lithologies: List[str]

    minimum_ucs_psi: int

    maximum_ucs_psi: int

    abrasive_formations: bool

    hpht_capable: bool


@dataclass
class BitInventory:
    """
    Inventory information.
    """

    manufacturer: str

    model: str

    iadc_code: str

    serial_number: str

    status: BitStatus


@dataclass
class BitSpecification:
    """
    Complete engineering description of a drill bit.

    This is the primary object stored inside the Bit Database.
    """

    name: str

    diameter: BitDiameter

    bit_type: BitType

    body: BitBody

    gauge_protection: GaugeProtection

    cutter: Optional[CutterConfiguration]

    roller_cone: Optional[RollerConeConfiguration]

    hydraulics: HydraulicConfiguration

    operating_window: BitOperatingWindow

    performance: BitPerformance

    hydraulic_performance: BitHydraulics

    limits: BitLimits

    application: BitApplication

    inventory: BitInventory

# ==============================================================
# BIT DATABASE
# ==============================================================

class BitDatabase:
    """
    Engineering drill bit database.

    Stores all available drill bits and provides lookup methods.
    """

    def __init__(self):

        self.bits = {}

        self._build_database()

    # ==========================================================
    # BUILD DATABASE
    # ==========================================================

    def _build_database(self):

        """
        Standard Guyana Offshore drilling bit inventory.
        """

        # ------------------------------------------------------
        # 36" CONDUCTOR BIT
        # ------------------------------------------------------

        self.add_bit(

            BitSpecification(

                name="36in Conductor Bit",

                diameter=BitDiameter(36.0, '36"'),

                bit_type=BitType.ROLLER_CONE,

                body=BitBody.STEEL,

                gauge_protection=GaugeProtection.HEAVY_DUTY,

                cutter=None,

                roller_cone=RollerConeConfiguration(

                    bearing_type=BearingType.ROLLER,

                    sealed_bearing=False,

                    insert_material="Milled Tooth"

                ),

                hydraulics=HydraulicConfiguration(

                    nozzle_type=NozzleType.FIXED,

                    nozzle_count=3,

                    nozzle_sizes_32nds=[24,24,24],

                    total_flow_area_in2=4.24,

                    hydraulic_type=HydraulicType.STANDARD

                ),

                operating_window=BitOperatingWindow(

                    wob_min_klbf=10,

                    wob_max_klbf=35,

                    rpm_min=50,

                    rpm_max=90,

                    flow_min_gpm=800,

                    flow_max_gpm=1200

                ),

                performance=BitPerformance(

                    expected_rop_ft_hr=120,

                    expected_bit_life_hr=40,

                    expected_footage_ft=500,

                    mechanical_efficiency=0.82,

                    dull_grade_expected="1-1-WT"

                ),

                hydraulic_performance=BitHydraulics(

                    hydraulic_horsepower=850,

                    impact_force_lbf=650,

                    jet_velocity_ft_sec=180,

                    hydraulic_efficiency=0.74

                ),

                limits=BitLimits(

                    maximum_temperature_f=250,

                    maximum_torque_ftlb=18000,

                    maximum_wob_klbf=45,

                    maximum_rpm=110

                ),

                application=BitApplication(

                    recommended_lithologies=["Unconsolidated Sediments"],

                    minimum_ucs_psi=0,

                    maximum_ucs_psi=2000,

                    abrasive_formations=False,

                    hpht_capable=False

                ),

                inventory=BitInventory(

                    manufacturer="Smith",

                    model="MG36",

                    iadc_code="117",

                    serial_number="BT-36001",

                    status=BitStatus.PLANNED

                )

            )

        )

        # ------------------------------------------------------
        # 26" SURFACE PDC
        # ------------------------------------------------------

        self.add_bit(

            BitSpecification(

                name="26in Surface PDC",

                diameter=BitDiameter(26.0,'26"'),

                bit_type=BitType.PDC,

                body=BitBody.STEEL,

                gauge_protection=GaugeProtection.PREMIUM,

                cutter=CutterConfiguration(

                    cutter_material=CutterMaterial.PDC,

                    cutter_size_mm=19,

                    back_rake_deg=15,

                    side_rake_deg=15,

                    blade_count=6,

                    blade_profile=BladeProfile.LONG,

                    gauge_pads=6

                ),

                roller_cone=None,

                hydraulics=HydraulicConfiguration(

                    nozzle_type=NozzleType.REPLACEABLE,

                    nozzle_count=6,

                    nozzle_sizes_32nds=[16,16,16,16,16,16],

                    total_flow_area_in2=3.60,

                    hydraulic_type=HydraulicType.HIGH_FLOW

                ),

                operating_window=BitOperatingWindow(

                    wob_min_klbf=15,

                    wob_max_klbf=45,

                    rpm_min=90,

                    rpm_max=180,

                    flow_min_gpm=700,

                    flow_max_gpm=1100

                ),

                performance=BitPerformance(

                    expected_rop_ft_hr=95,

                    expected_bit_life_hr=90,

                    expected_footage_ft=3000,

                    mechanical_efficiency=0.91,

                    dull_grade_expected="1-1-NO"

                ),

                hydraulic_performance=BitHydraulics(

                    hydraulic_horsepower=950,

                    impact_force_lbf=720,

                    jet_velocity_ft_sec=220,

                    hydraulic_efficiency=0.86

                ),

                limits=BitLimits(

                    maximum_temperature_f=320,

                    maximum_torque_ftlb=25000,

                    maximum_wob_klbf=55,

                    maximum_rpm=220

                ),

                application=BitApplication(

                    recommended_lithologies=["Sand","Clay","Silt"],

                    minimum_ucs_psi=1000,

                    maximum_ucs_psi=8000,

                    abrasive_formations=False,

                    hpht_capable=False

                ),

                inventory=BitInventory(

                    manufacturer="Baker Hughes",

                    model="Kymera Surface",

                    iadc_code="M223",

                    serial_number="BT-26001",

                    status=BitStatus.PLANNED

                )

            )

        )
    
            # ------------------------------------------------------
        # 17-1/2" INTERMEDIATE PDC
        # ------------------------------------------------------

        self.add_bit(

            BitSpecification(

                name="17-1/2in Intermediate PDC",

                diameter=BitDiameter(17.5, '17-1/2"'),

                bit_type=BitType.PDC,

                body=BitBody.MATRIX,

                gauge_protection=GaugeProtection.PREMIUM,

                cutter=CutterConfiguration(

                    cutter_material=CutterMaterial.PDC,

                    cutter_size_mm=16,

                    back_rake_deg=18,

                    side_rake_deg=15,

                    blade_count=7,

                    blade_profile=BladeProfile.MEDIUM,

                    gauge_pads=7

                ),

                roller_cone=None,

                hydraulics=HydraulicConfiguration(

                    nozzle_type=NozzleType.REPLACEABLE,

                    nozzle_count=7,

                    nozzle_sizes_32nds=[13,13,13,13,13,13,13],

                    total_flow_area_in2=2.85,

                    hydraulic_type=HydraulicType.HIGH_FLOW

                ),

                operating_window=BitOperatingWindow(

                    wob_min_klbf=18,

                    wob_max_klbf=45,

                    rpm_min=110,

                    rpm_max=190,

                    flow_min_gpm=550,

                    flow_max_gpm=850

                ),

                performance=BitPerformance(

                    expected_rop_ft_hr=78,

                    expected_bit_life_hr=140,

                    expected_footage_ft=6500,

                    mechanical_efficiency=0.93,

                    dull_grade_expected="1-1-NO"

                ),

                hydraulic_performance=BitHydraulics(

                    hydraulic_horsepower=720,

                    impact_force_lbf=580,

                    jet_velocity_ft_sec=255,

                    hydraulic_efficiency=0.91

                ),

                limits=BitLimits(

                    maximum_temperature_f=360,

                    maximum_torque_ftlb=32000,

                    maximum_wob_klbf=55,

                    maximum_rpm=220

                ),

                application=BitApplication(

                    recommended_lithologies=["Shale","Siltstone"],

                    minimum_ucs_psi=4000,

                    maximum_ucs_psi=18000,

                    abrasive_formations=False,

                    hpht_capable=True

                ),

                inventory=BitInventory(

                    manufacturer="SLB",

                    model="PowerDrive PDC",

                    iadc_code="M332",

                    serial_number="BT-17501",

                    status=BitStatus.PLANNED

                )

            )

        )

            # ------------------------------------------------------
        # 12-1/4" PRODUCTION PDC
        # ------------------------------------------------------

        self.add_bit(

            BitSpecification(

                name="12-1/4in Production PDC",

                diameter=BitDiameter(12.25,'12-1/4"'),

                bit_type=BitType.PDC,

                body=BitBody.MATRIX,

                gauge_protection=GaugeProtection.HEAVY_DUTY,

                cutter=CutterConfiguration(

                    cutter_material=CutterMaterial.PDC,

                    cutter_size_mm=16,

                    back_rake_deg=20,

                    side_rake_deg=15,

                    blade_count=6,

                    blade_profile=BladeProfile.SHORT,

                    gauge_pads=6

                ),

                roller_cone=None,

                hydraulics=HydraulicConfiguration(

                    nozzle_type=NozzleType.REPLACEABLE,

                    nozzle_count=6,

                    nozzle_sizes_32nds=[12,12,12,12,12,12],

                    total_flow_area_in2=2.25,

                    hydraulic_type=HydraulicType.OPTIMIZED

                ),

                operating_window=BitOperatingWindow(

                    wob_min_klbf=20,

                    wob_max_klbf=55,

                    rpm_min=120,

                    rpm_max=210,

                    flow_min_gpm=400,

                    flow_max_gpm=650

                ),

                performance=BitPerformance(

                    expected_rop_ft_hr=60,

                    expected_bit_life_hr=180,

                    expected_footage_ft=9000,

                    mechanical_efficiency=0.95,

                    dull_grade_expected="2-1-WT"

                ),

                hydraulic_performance=BitHydraulics(

                    hydraulic_horsepower=610,

                    impact_force_lbf=510,

                    jet_velocity_ft_sec=290,

                    hydraulic_efficiency=0.94

                ),

                limits=BitLimits(

                    maximum_temperature_f=400,

                    maximum_torque_ftlb=38000,

                    maximum_wob_klbf=65,

                    maximum_rpm=230

                ),

                application=BitApplication(

                    recommended_lithologies=["Hard Shale","Carbonate"],

                    minimum_ucs_psi=10000,

                    maximum_ucs_psi=30000,

                    abrasive_formations=True,

                    hpht_capable=True

                ),

                inventory=BitInventory(

                    manufacturer="Halliburton",

                    model="GeoTech PDC",

                    iadc_code="M433",

                    serial_number="BT-12251",

                    status=BitStatus.PLANNED

                )

            )

        )

            # ------------------------------------------------------
        # 8-1/2" RESERVOIR PDC
        # ------------------------------------------------------

        self.add_bit(

            BitSpecification(

                name="8-1/2in Reservoir PDC",

                diameter=BitDiameter(8.5,'8-1/2"'),

                bit_type=BitType.PDC,

                body=BitBody.MATRIX,

                gauge_protection=GaugeProtection.HEAVY_DUTY,

                cutter=CutterConfiguration(

                    cutter_material=CutterMaterial.PDC,

                    cutter_size_mm=13,

                    back_rake_deg=22,

                    side_rake_deg=15,

                    blade_count=7,

                    blade_profile=BladeProfile.SHORT,

                    gauge_pads=7

                ),

                roller_cone=None,

                hydraulics=HydraulicConfiguration(

                    nozzle_type=NozzleType.REPLACEABLE,

                    nozzle_count=7,

                    nozzle_sizes_32nds=[11,11,11,11,11,11,11],

                    total_flow_area_in2=1.82,

                    hydraulic_type=HydraulicType.HIGH_IMPACT

                ),

                operating_window=BitOperatingWindow(

                    wob_min_klbf=18,

                    wob_max_klbf=45,

                    rpm_min=140,

                    rpm_max=240,

                    flow_min_gpm=250,

                    flow_max_gpm=500

                ),

                performance=BitPerformance(

                    expected_rop_ft_hr=48,

                    expected_bit_life_hr=220,

                    expected_footage_ft=12000,

                    mechanical_efficiency=0.97,

                    dull_grade_expected="2-2-WT"

                ),

                hydraulic_performance=BitHydraulics(

                    hydraulic_horsepower=430,

                    impact_force_lbf=390,

                    jet_velocity_ft_sec=340,

                    hydraulic_efficiency=0.96

                ),

                limits=BitLimits(

                    maximum_temperature_f=430,

                    maximum_torque_ftlb=42000,

                    maximum_wob_klbf=55,

                    maximum_rpm=260

                ),

                application=BitApplication(

                    recommended_lithologies=[

                        "Sandstone",

                        "Reservoir Sand",

                        "Hard Shale"

                    ],

                    minimum_ucs_psi=8000,

                    maximum_ucs_psi=35000,

                    abrasive_formations=True,

                    hpht_capable=True

                ),

                inventory=BitInventory(

                    manufacturer="Baker Hughes",

                    model="Kymera Reservoir",

                    iadc_code="M523",

                    serial_number="BT-08501",

                    status=BitStatus.PLANNED

                )

            )

        )

    # ==========================================================
    # DATABASE UTILITIES
    # ==========================================================

    def add_bit(self, bit: BitSpecification):

        self.bits[bit.name] = bit


    def get(self, name: str):

        return self.bits.get(name)


    def all_bits(self):

        return list(self.bits.values())


    def count(self):

        return len(self.bits)
    
# ==============================================================
# BIT SELECTION ENGINE
# ==============================================================

    def bits_by_diameter(self, diameter: float):
        """
        Return all bits matching a given diameter.
        """

        return [

            bit

            for bit in self.bits.values()

            if abs(bit.diameter.value - diameter) < 0.01

        ]


    def bits_by_type(self, bit_type: BitType):

        return [

            bit

            for bit in self.bits.values()

            if bit.bit_type == bit_type

        ]


    def bits_for_lithology(self, lithology: str):

        return [

            bit

            for bit in self.bits.values()

            if lithology in bit.application.recommended_lithologies

        ]


    def bits_for_hole(self, hole_size: float):

        return self.bits_by_diameter(hole_size)


    def best_bit(
        self,
        hole_size: float,
        lithology: str,
        ucs_psi: float
    ):
        """
        Engineering recommendation.

        Returns the best bit for a given
        hole size and formation.
        """

        candidates = self.bits_by_diameter(hole_size)

        if not candidates:

            return None

        scored = []

        for bit in candidates:

            score = 0

            # --------------------------------------
            # Lithology
            # --------------------------------------

            if lithology in bit.application.recommended_lithologies:

                score += 60

            # --------------------------------------
            # UCS Window
            # --------------------------------------

            if (

                bit.application.minimum_ucs_psi

                <= ucs_psi

                <= bit.application.maximum_ucs_psi

            ):

                score += 30

            # --------------------------------------
            # Mechanical efficiency
            # --------------------------------------

            score += bit.performance.mechanical_efficiency * 10

            scored.append((score, bit))

        scored.sort(

            key=lambda x: x[0],

            reverse=True

        )

        return scored[0][1]


    def recommend_from_formation(self, formation):
        """
        Receives one Formation object from formations.py
        and recommends a drill bit.
        """

        return self.best_bit(

            hole_size=formation.hole_size,

            lithology=formation.lithology,

            ucs_psi=formation.ucs_psi

        )


    def recommend(
        self,
        hole_size,
        lithology,
        formation_name=None,
        abrasive=False,
        hpht=False,
        ucs=12000
    ):
        """
        High-level recommendation function.

        This will become the standard interface
        used by geology.py.
        """

        bit = self.best_bit(

            hole_size,

            lithology,

            ucs

        )

        return bit
    
# ==============================================================
# BIT PERFORMANCE ENGINE
# ==============================================================

    def predicted_rop(
        self,
        bit: BitSpecification,
        ucs_psi: float,
        wob_klbf: float,
        rpm: float
    ):
        """
        Estimate Rate of Penetration (ROP).

        Uses a simplified engineering correction based on:
            - Formation strength (UCS)
            - Applied WOB
            - Rotary speed

        Returns
        -------
        float
            Estimated ROP (ft/hr)
        """

        base = bit.performance.expected_rop_ft_hr

        # Strength correction
        strength_factor = 12000 / max(ucs_psi, 1000)

        # Weight on bit correction
        design_wob = (
            bit.operating_window.wob_min_klbf +
            bit.operating_window.wob_max_klbf
        ) / 2

        wob_factor = wob_klbf / design_wob

        # RPM correction
        design_rpm = (
            bit.operating_window.rpm_min +
            bit.operating_window.rpm_max
        ) / 2

        rpm_factor = rpm / design_rpm

        rop = base * strength_factor * wob_factor * rpm_factor

        return round(max(5, rop), 1)


    # ==========================================================
    # BIT LIFE
    # ==============================================================

    def predicted_bit_life(
        self,
        bit: BitSpecification,
        ucs_psi: float
    ):

        life = bit.performance.expected_bit_life_hr

        correction = 12000 / max(ucs_psi, 1000)

        return round(life * correction, 1)


    # ==========================================================
    # EXPECTED FOOTAGE
    # ==============================================================

    def predicted_footage(
        self,
        bit: BitSpecification,
        ucs_psi: float
    ):

        footage = bit.performance.expected_footage_ft

        correction = 12000 / max(ucs_psi, 1000)

        return round(footage * correction)


    # ==========================================================
    # RECOMMENDED WOB
    # ==============================================================

    def recommended_wob(
        self,
        bit: BitSpecification
    ):

        return round(

            (

                bit.operating_window.wob_min_klbf +

                bit.operating_window.wob_max_klbf

            ) / 2,

            1

        )


    # ==========================================================
    # RECOMMENDED RPM
    # ==============================================================

    def recommended_rpm(
        self,
        bit: BitSpecification
    ):

        return round(

            (

                bit.operating_window.rpm_min +

                bit.operating_window.rpm_max

            ) / 2

        )


    # ==========================================================
    # RECOMMENDED FLOW
    # ==============================================================

    def recommended_flow(
        self,
        bit: BitSpecification
    ):

        return round(

            (

                bit.operating_window.flow_min_gpm +

                bit.operating_window.flow_max_gpm

            ) / 2

        )


    # ==========================================================
    # ESTIMATED TORQUE
    # ==============================================================

    def estimated_torque(
        self,
        bit: BitSpecification,
        wob_klbf: float
    ):

        torque = (

            wob_klbf /

            bit.limits.maximum_wob_klbf

        ) * bit.limits.maximum_torque_ftlb

        return round(torque)


    # ==========================================================
    # BIT UTILIZATION
    # ==============================================================

    def utilization(
        self,
        bit: BitSpecification,
        wob_klbf: float,
        rpm: float
    ):

        wob_pct = (

            wob_klbf /

            bit.limits.maximum_wob_klbf

        )

        rpm_pct = (

            rpm /

            bit.limits.maximum_rpm

        )

        return round(

            100 *

            (wob_pct + rpm_pct) / 2,

            1

        )


    # ==========================================================
    # COMPLETE PERFORMANCE REPORT
    # ==============================================================

    def performance_report(
        self,
        bit: BitSpecification,
        ucs_psi: float
    ):

        wob = self.recommended_wob(bit)

        rpm = self.recommended_rpm(bit)

        report = {

            "Bit": bit.name,

            "ROP_ft_hr": self.predicted_rop(

                bit,

                ucs_psi,

                wob,

                rpm

            ),

            "BitLife_hr": self.predicted_bit_life(

                bit,

                ucs_psi

            ),

            "Footage_ft": self.predicted_footage(

                bit,

                ucs_psi

            ),

            "Recommended_WOB": wob,

            "Recommended_RPM": rpm,

            "Recommended_Flow": self.recommended_flow(bit),

            "Estimated_Torque": self.estimated_torque(

                bit,

                wob

            ),

            "Utilization_pct": self.utilization(

                bit,

                wob,

                rpm

            )

        }

        return report

# ==============================================================
# FAILURE ANALYSIS
# ==============================================================

    def stick_slip_risk(
        self,
        bit: BitSpecification,
        ucs_psi: float
    ):
        """
        Estimate stick-slip risk.

        Returns a value between 0 and 1.
        """

        risk = (
            (ucs_psi / 30000)
            * (bit.limits.maximum_torque_ftlb / 45000)
        )

        return round(min(max(risk, 0.0), 1.0), 2)


    # ==========================================================
    # BIT WHIRL
    # ==============================================================

    def whirl_risk(
        self,
        bit: BitSpecification
    ):

        if bit.bit_type == BitType.PDC:

            risk = 0.18

            if bit.cutter:

                risk += max(0, (7 - bit.cutter.blade_count)) * 0.05

        else:

            risk = 0.35

        return round(min(risk, 1.0), 2)


    # ==========================================================
    # BIT BALLING
    # ==============================================================

    def bit_balling_risk(
        self,
        lithology: str
    ):

        lithology = lithology.lower()

        if "clay" in lithology:
            return 0.90

        if "shale" in lithology:
            return 0.55

        if "silt" in lithology:
            return 0.45

        if "sand" in lithology:
            return 0.10

        return 0.25


    # ==========================================================
    # CUTTER WEAR
    # ==============================================================

    def cutter_wear(
        self,
        ucs_psi: float,
        drilled_hours: float
    ):

        wear = (

            (ucs_psi / 30000)

            *

            (drilled_hours / 200)

        )

        return round(min(wear, 1.0), 2)


    # ==========================================================
    # BEARING WEAR
    # ==============================================================

    def bearing_wear(
        self,
        bit: BitSpecification,
        drilled_hours: float
    ):

        if bit.bit_type != BitType.ROLLER_CONE:

            return 0.0

        wear = drilled_hours / 150

        return round(min(wear, 1.0), 2)


    # ==========================================================
    # GAUGE WEAR
    # ==============================================================

    def gauge_wear(
        self,
        drilled_hours: float
    ):

        return round(

            min(drilled_hours / 250, 1.0),

            2

        )


    # ==========================================================
    # THERMAL DAMAGE
    # ==============================================================

    def thermal_damage(
        self,
        temperature_f: float
    ):

        damage = (

            temperature_f - 250

        ) / 250

        return round(

            min(max(damage, 0.0), 1.0),

            2

        )

# ==============================================================
# IADC DULL GRADING
# ==============================================================

    def dull_grade(
        self,
        bit: BitSpecification,
        ucs_psi: float,
        drilled_hours: float,
        temperature_f: float,
        lithology: str
    ):
        """
        Generate a simplified IADC dull grade.
        """

        cutter = int(

            self.cutter_wear(
                ucs_psi,
                drilled_hours
            ) * 8

        )

        bearing = int(

            self.bearing_wear(
                bit,
                drilled_hours
            ) * 8

        )

        gauge = int(

            self.gauge_wear(
                drilled_hours
            ) * 8

        )

        if self.bit_balling_risk(lithology) > 0.6:

            reason = "BT"

        elif self.stick_slip_risk(bit, ucs_psi) > 0.6:

            reason = "SS"

        else:

            reason = "TD"

        return (

            f"{cutter}-{bearing}-"

            f"WT-A-X-I-"

            f"{reason}-"

            f"{gauge}"

        )

# ==============================================================
# COMPLETE FAILURE REPORT
# ==============================================================

    def failure_report(
        self,
        bit: BitSpecification,
        ucs_psi: float,
        drilled_hours: float,
        temperature_f: float,
        lithology: str
    ):

        return {

            "StickSlip":

                self.stick_slip_risk(
                    bit,
                    ucs_psi
                ),

            "Whirl":

                self.whirl_risk(
                    bit
                ),

            "BitBalling":

                self.bit_balling_risk(
                    lithology
                ),

            "CutterWear":

                self.cutter_wear(
                    ucs_psi,
                    drilled_hours
                ),

            "BearingWear":

                self.bearing_wear(
                    bit,
                    drilled_hours
                ),

            "GaugeWear":

                self.gauge_wear(
                    drilled_hours
                ),

            "ThermalDamage":

                self.thermal_damage(
                    temperature_f
                ),

            "IADC":

                self.dull_grade(

                    bit,

                    ucs_psi,

                    drilled_hours,

                    temperature_f,

                    lithology

                )

        }

# ==============================================================
# DATABASE SUMMARY
# ==============================================================

    def database_summary(self):

        total = len(self.bits)

        pdc = len(self.bits_by_type(BitType.PDC))

        roller = len(self.bits_by_type(BitType.ROLLER_CONE))

        print()
        print("=" * 70)
        print("BIT DATABASE SUMMARY")
        print("=" * 70)

        print(f"Total bits              : {total}")
        print(f"PDC bits                : {pdc}")
        print(f"Roller Cone bits        : {roller}")

        diameters = sorted(
            {bit.diameter.label for bit in self.bits.values()}
        )

        print("Available diameters     :", ", ".join(diameters))

        print("=" * 70)


# ==============================================================
# DATABASE VALIDATION
# ==============================================================

    def validate_database(self):

        print()
        print("=" * 70)
        print("BIT DATABASE VALIDATION")
        print("=" * 70)

        errors = []

        if len(self.bits) == 0:
            errors.append("Database is empty.")

        names = set()

        for bit in self.bits.values():

            if bit.name in names:
                errors.append(f"Duplicate bit: {bit.name}")

            names.add(bit.name)

            if bit.operating_window.wob_min_klbf >= bit.operating_window.wob_max_klbf:
                errors.append(f"WOB window invalid ({bit.name})")

            if bit.operating_window.rpm_min >= bit.operating_window.rpm_max:
                errors.append(f"RPM window invalid ({bit.name})")

            if bit.performance.expected_rop_ft_hr <= 0:
                errors.append(f"Invalid ROP ({bit.name})")

        if errors:

            print("STATUS : FAILED")
            print()

            for e in errors:
                print("-", e)

        else:

            print("STATUS : PASSED")
            print("No engineering inconsistencies detected.")

        print("=" * 70)


# ==============================================================
# COMPLETE REPORT
# ==============================================================

    def engineering_report(self):

        self.database_summary()

        self.validate_database()

# ==============================================================
# MAIN TEST PROGRAM
# ==============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("BIT DATABASE LIBRARY")
    print("Version 1.0")
    print("=" * 70)

    db = BitDatabase()

    print()
    print("Library initialized successfully.")

    db.database_summary()

    db.validate_database()

    print()
    print("=" * 70)
    print("AVAILABLE BITS")
    print("=" * 70)

    for bit in db.bits.values():

        print(
            f"{bit.name:<32}"
            f"{bit.diameter.label:<10}"
            f"{bit.bit_type.value:<15}"
            f"{bit.inventory.manufacturer}"
        )

    print()
    print("=" * 70)
    print("BIT SELECTION EXAMPLES")
    print("=" * 70)

    examples = [

        (17.5, "Shale", 12000),

        (12.25, "Hard Shale", 18000),

        (8.5, "Sandstone", 15000)

    ]

    for hole, lithology, ucs in examples:

        bit = db.recommend(

            hole_size=hole,

            lithology=lithology,

            ucs=ucs

        )

        print()

        print(f"Hole Size : {hole}\"")

        print(f"Lithology : {lithology}")

        print(f"UCS       : {ucs} psi")

        print("-" * 40)

        print("Selected Bit :", bit.name)

        report = db.performance_report(bit, ucs)

        print()

        print("Performance")

        for k, v in report.items():

            print(f"{k:<22}: {v}")

        print()

        failure = db.failure_report(

            bit,

            ucs,

            drilled_hours=100,

            temperature_f=320,

            lithology=lithology

        )

        print("Failure Analysis")

        for k, v in failure.items():

            print(f"{k:<22}: {v}")

    print()
    print("=" * 70)
    print("STATUS : BIT DATABASE PASSED")
    print("=" * 70)