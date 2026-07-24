"""
======================================================================
well_design.py

Guyana Offshore Drilling Analytics

Version : 1.3

Digital Well Architecture Library

Author:
Anibal Ceballos
(OpenAI Assisted)

======================================================================

PURPOSE

This module represents the complete engineering architecture
of an offshore well.

It is the engineering foundation used by:

    geology.py
    bits.py
    bha.py
    drilling_fluids.py
    hydraulics.py
    directional.py
    torque_drag.py
    drilling_engine.py

No engineering values should be hard-coded anywhere else in
the project.

======================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


# ==============================================================
# ENGINEERING ENUMERATIONS
# ==============================================================

class WellType(Enum):

    EXPLORATION = "Exploration"

    APPRAISAL = "Appraisal"

    DEVELOPMENT = "Development"

    INJECTION = "Injection"

    SIDETRACK = "Sidetrack"


class FieldType(Enum):

    ONSHORE = "Onshore"

    SHELF = "Shelf"

    DEEPWATER = "Deepwater"

    ULTRA_DEEPWATER = "Ultra Deepwater"

    HPHT = "HPHT"


class WellStatus(Enum):

    PLANNED = "Planned"

    DRILLING = "Drilling"

    COMPLETED = "Completed"

    ABANDONED = "Abandoned"


class HoleSectionType(Enum):

    CONDUCTOR = "Conductor"

    SURFACE = "Surface"

    INTERMEDIATE = "Intermediate"

    PRODUCTION = "Production"

    RESERVOIR = "Reservoir"


class MudSystem(Enum):

    SEAWATER = "Seawater"

    WBM = "Water Based Mud"

    SBM = "Synthetic Based Mud"

    OBM = "Oil Based Mud"


class CasingGrade(Enum):

    K55 = "K55"

    L80 = "L80"

    P110 = "P110"

    Q125 = "Q125"


class CompletionType(Enum):

    OPEN_HOLE = "Open Hole"

    CASED_HOLE = "Cased Hole"

    INTELLIGENT = "Intelligent"

    MULTILATERAL = "Multilateral"


# ==============================================================
# ENGINEERING DATA CLASSES
# ==============================================================

@dataclass(frozen=True)
class WellDiameter:
    """
    Engineering representation of any drilling diameter.
    """

    value: float

    label: str

    unit: str = "in"

    def __float__(self):

        return self.value

    def __str__(self):

        return self.label


@dataclass(slots=True)
class HoleSection:

    name: str

    top_depth_ft: float

    bottom_depth_ft: float

    hole: WellDiameter

    bit: WellDiameter

    mud_system: MudSystem

    description: str

    expected_section_days: float


@dataclass(slots=True)
class CasingSection:

    name: str

    casing: WellDiameter

    hole: WellDiameter

    setting_depth_ft: float

    cement_top_ft: float

    grade: CasingGrade

    weight_lb_ft: float

    connection: str

    drift_id_in: float


@dataclass(slots=True)
class CementSection:

    casing_name: str

    slurry_type: str

    top_depth_ft: float

    bottom_depth_ft: float

    lead_yield_ft3_sk: float

    tail_yield_ft3_sk: float


@dataclass(slots=True)
class TrajectorySection:

    name: str

    md_from_ft: float

    md_to_ft: float

    inclination_start_deg: float

    inclination_end_deg: float

    azimuth_deg: float

    max_dogleg_deg100ft: float


@dataclass(slots=True)
class BOPConfiguration:

    pressure_rating_psi: int

    annular_preventers: int

    ram_preventers: int

    shear_ram: bool

    diverter: bool


@dataclass(slots=True)
class CompletionConfiguration:

    completion_type: CompletionType

    tubing: WellDiameter

    liner: WellDiameter

    packer: str

    sand_control: str


# ==============================================================
# DEFAULT WELL PARAMETERS
# ==============================================================

DEFAULT_WELL_NAME = "Guyana Development Well"

DEFAULT_OPERATOR = "Example Operator"

DEFAULT_FIELD = "Stabroek"

DEFAULT_COUNTRY = "Guyana"

DEFAULT_FIELD_TYPE = FieldType.DEEPWATER

DEFAULT_WELL_TYPE = WellType.DEVELOPMENT

DEFAULT_STATUS = WellStatus.PLANNED

DEFAULT_WATER_DEPTH_FT = 6200

DEFAULT_TOTAL_DEPTH_FT = 21000

DEFAULT_KB_ELEVATION_FT = 85

DEFAULT_LATITUDE = 5.80

DEFAULT_LONGITUDE = -57.30

DEFAULT_RIG_NAME = "Deepwater Drillship"

DEFAULT_BOP_PRESSURE = 15000

# ==============================================================
# WELL DESIGN CLASS
# ==============================================================

class WellDesign:
    """
    Digital Engineering Representation of an Offshore Well.

    This object stores every engineering parameter required by
    the drilling simulator.

    All engineering libraries (geology, hydraulics, BHA,
    torque & drag, drilling mechanics, etc.) should query this
    object instead of hard-coding engineering values.
    """

    # ==========================================================
    # CONSTRUCTOR
    # ==========================================================

    def __init__(self):

        # ------------------------------------------------------
        # GENERAL INFORMATION
        # ------------------------------------------------------

        self.well_name = DEFAULT_WELL_NAME

        self.operator = DEFAULT_OPERATOR

        self.field = DEFAULT_FIELD

        self.country = DEFAULT_COUNTRY

        self.field_type = DEFAULT_FIELD_TYPE

        self.well_type = DEFAULT_WELL_TYPE

        self.status = DEFAULT_STATUS

        # ------------------------------------------------------
        # LOCATION
        # ------------------------------------------------------

        self.latitude = DEFAULT_LATITUDE

        self.longitude = DEFAULT_LONGITUDE

        self.water_depth_ft = DEFAULT_WATER_DEPTH_FT

        self.total_depth_ft = DEFAULT_TOTAL_DEPTH_FT

        self.kb_elevation_ft = DEFAULT_KB_ELEVATION_FT

        # ------------------------------------------------------
        # RIG
        # ------------------------------------------------------

        self.rig_name = DEFAULT_RIG_NAME

        self.bop_pressure_rating = DEFAULT_BOP_PRESSURE

        # ------------------------------------------------------
        # ENGINEERING PROGRAMS
        # ------------------------------------------------------

        self.hole_program = self._build_hole_program()

        self.casing_program = self._build_casing_program()

        self.cement_program = self._build_cement_program()

        self.trajectory_program = self._build_trajectory_program()

        self.bop_configuration = self._build_bop_configuration()

        self.completion_configuration = self._build_completion()

    # ==========================================================
    # BASIC PROPERTIES
    # ==========================================================

    @property
    def total_sections(self):

        return len(self.hole_program)


    @property
    def total_casing_strings(self):

        return len(self.casing_program)


    @property
    def max_depth(self):

        return self.total_depth_ft


    @property
    def water_depth(self):

        return self.water_depth_ft


    @property
    def kb(self):

        return self.kb_elevation_ft


    @property
    def operator_name(self):

        return self.operator


    @property
    def field_name(self):

        return self.field


    @property
    def rig(self):

        return self.rig_name
    
        # ==========================================================
    # HOLE PROGRAM
    # ==========================================================

    def _build_hole_program(self) -> List[HoleSection]:

        return [

            HoleSection(
                name="Conductor",
                top_depth_ft=0,
                bottom_depth_ft=300,
                hole=WellDiameter(36.0, '36"'),
                bit=WellDiameter(36.0, '36"'),
                mud_system=MudSystem.SEAWATER,
                description="Jet-in conductor section",
                expected_section_days=1.5,
            ),

            HoleSection(
                name="Surface",
                top_depth_ft=300,
                bottom_depth_ft=3000,
                hole=WellDiameter(26.0, '26"'),
                bit=WellDiameter(26.0, '26"'),
                mud_system=MudSystem.WBM,
                description="Surface hole",
                expected_section_days=5.0,
            ),

            HoleSection(
                name="Intermediate",
                top_depth_ft=3000,
                bottom_depth_ft=9000,
                hole=WellDiameter(17.5, '17-1/2"'),
                bit=WellDiameter(17.5, '17-1/2"'),
                mud_system=MudSystem.WBM,
                description="Intermediate section",
                expected_section_days=12.0,
            ),

            HoleSection(
                name="Production",
                top_depth_ft=9000,
                bottom_depth_ft=18000,
                hole=WellDiameter(12.25, '12-1/4"'),
                bit=WellDiameter(12.25, '12-1/4"'),
                mud_system=MudSystem.SBM,
                description="Production hole",
                expected_section_days=16.0,
            ),

            HoleSection(
                name="Reservoir",
                top_depth_ft=18000,
                bottom_depth_ft=self.total_depth_ft,
                hole=WellDiameter(8.5, '8-1/2"'),
                bit=WellDiameter(8.5, '8-1/2"'),
                mud_system=MudSystem.SBM,
                description="Reservoir section",
                expected_section_days=9.0,
            )

        ]

    # ==========================================================
    # CASING PROGRAM
    # ==========================================================

    def _build_casing_program(self) -> List[CasingSection]:

        return [

            CasingSection(
                name="Conductor",
                casing=WellDiameter(30.0, '30"'),
                hole=WellDiameter(36.0, '36"'),
                setting_depth_ft=300,
                cement_top_ft=0,
                grade=CasingGrade.K55,
                weight_lb_ft=309,
                connection="BTC",
                drift_id_in=29.0,
            ),

            CasingSection(
                name="Surface",
                casing=WellDiameter(20.0, '20"'),
                hole=WellDiameter(26.0, '26"'),
                setting_depth_ft=3000,
                cement_top_ft=0,
                grade=CasingGrade.K55,
                weight_lb_ft=133,
                connection="BTC",
                drift_id_in=19.1,
            ),

            CasingSection(
                name="Intermediate",
                casing=WellDiameter(13.375, '13-3/8"'),
                hole=WellDiameter(17.5, '17-1/2"'),
                setting_depth_ft=9000,
                cement_top_ft=2500,
                grade=CasingGrade.L80,
                weight_lb_ft=72,
                connection="Premium",
                drift_id_in=12.347,
            ),

            CasingSection(
                name="Production",
                casing=WellDiameter(9.625, '9-5/8"'),
                hole=WellDiameter(12.25, '12-1/4"'),
                setting_depth_ft=18000,
                cement_top_ft=9000,
                grade=CasingGrade.P110,
                weight_lb_ft=53.5,
                connection="Premium",
                drift_id_in=8.681,
            ),

            CasingSection(
                name="Production Liner",
                casing=WellDiameter(7.0, '7"'),
                hole=WellDiameter(8.5, '8-1/2"'),
                setting_depth_ft=self.total_depth_ft,
                cement_top_ft=17000,
                grade=CasingGrade.P110,
                weight_lb_ft=32.0,
                connection="Premium",
                drift_id_in=6.276,
            )

        ]
    
        # ==========================================================
    # CEMENT PROGRAM
    # ==========================================================

    def _build_cement_program(self) -> List[CementSection]:

        return [

            CementSection(
                casing_name="Conductor",
                slurry_type="Class G + Bentonite",
                top_depth_ft=0,
                bottom_depth_ft=300,
                lead_yield_ft3_sk=2.10,
                tail_yield_ft3_sk=1.18,
            ),

            CementSection(
                casing_name="Surface",
                slurry_type="Class G",
                top_depth_ft=0,
                bottom_depth_ft=3000,
                lead_yield_ft3_sk=1.95,
                tail_yield_ft3_sk=1.18,
            ),

            CementSection(
                casing_name="Intermediate",
                slurry_type="Class G + Silica",
                top_depth_ft=2500,
                bottom_depth_ft=9000,
                lead_yield_ft3_sk=1.82,
                tail_yield_ft3_sk=1.15,
            ),

            CementSection(
                casing_name="Production",
                slurry_type="HPHT Class G",
                top_depth_ft=9000,
                bottom_depth_ft=18000,
                lead_yield_ft3_sk=1.60,
                tail_yield_ft3_sk=1.08,
            ),

            CementSection(
                casing_name="Production Liner",
                slurry_type="HPHT Lightweight",
                top_depth_ft=17000,
                bottom_depth_ft=21000,
                lead_yield_ft3_sk=1.45,
                tail_yield_ft3_sk=1.05,
            ),

        ]

    # ==========================================================
    # TRAJECTORY PROGRAM
    # ==========================================================

    def _build_trajectory_program(self) -> List[TrajectorySection]:

        return [

            TrajectorySection(
                name="Vertical",
                md_from_ft=0,
                md_to_ft=4500,
                inclination_start_deg=0.0,
                inclination_end_deg=0.0,
                azimuth_deg=0.0,
                max_dogleg_deg100ft=0.0,
            ),

            TrajectorySection(
                name="Build",
                md_from_ft=4500,
                md_to_ft=9000,
                inclination_start_deg=0.0,
                inclination_end_deg=35.0,
                azimuth_deg=115.0,
                max_dogleg_deg100ft=2.5,
            ),

            TrajectorySection(
                name="Hold",
                md_from_ft=9000,
                md_to_ft=16500,
                inclination_start_deg=35.0,
                inclination_end_deg=35.0,
                azimuth_deg=115.0,
                max_dogleg_deg100ft=1.5,
            ),

            TrajectorySection(
                name="Landing",
                md_from_ft=16500,
                md_to_ft=21000,
                inclination_start_deg=35.0,
                inclination_end_deg=90.0,
                azimuth_deg=115.0,
                max_dogleg_deg100ft=3.0,
            ),

        ]

    # ==========================================================
    # BOP CONFIGURATION
    # ==========================================================

    def _build_bop_configuration(self) -> BOPConfiguration:

        return BOPConfiguration(

            pressure_rating_psi=15000,

            annular_preventers=2,

            ram_preventers=5,

            shear_ram=True,

            diverter=True,

        )

    # ==========================================================
    # COMPLETION CONFIGURATION
    # ==========================================================

    def _build_completion(self) -> CompletionConfiguration:

        return CompletionConfiguration(

            completion_type=CompletionType.CASED_HOLE,

            tubing=WellDiameter(
                value=3.5,
                label='3-1/2"'
            ),

            liner=WellDiameter(
                value=7.0,
                label='7"'
            ),

            packer="Permanent HPHT",

            sand_control="Premium Screens",

        )
    
        # ==========================================================
    # INTERNAL SEARCH METHODS
    # ==============================================================

    def current_section(self, depth_ft: float) -> HoleSection:
        """
        Returns the active hole section at the specified depth.
        """

        for section in self.hole_program:

            if section.top_depth_ft <= depth_ft < section.bottom_depth_ft:

                return section

        return self.hole_program[-1]


    def current_casing(self, depth_ft: float) -> CasingSection:
        """
        Returns the casing string that contains the specified depth.
        """

        for casing in self.casing_program:

            if depth_ft <= casing.setting_depth_ft:

                return casing

        return self.casing_program[-1]


    def current_trajectory(self, depth_ft: float) -> TrajectorySection:
        """
        Returns the trajectory segment corresponding to the specified depth.
        """

        for segment in self.trajectory_program:

            if segment.md_from_ft <= depth_ft < segment.md_to_ft:

                return segment

        return self.trajectory_program[-1]


    # ==========================================================
    # HOLE LOOKUPS
    # ==============================================================

    def section_name(self, depth_ft: float) -> str:

        return self.current_section(depth_ft).name


    def hole_size(self, depth_ft: float) -> float:

        return self.current_section(depth_ft).hole.value


    def hole_label(self, depth_ft: float) -> str:

        return self.current_section(depth_ft).hole.label


    def bit_size(self, depth_ft: float) -> float:

        return self.current_section(depth_ft).bit.value


    def bit_label(self, depth_ft: float) -> str:

        return self.current_section(depth_ft).bit.label


    def mud_system(self, depth_ft: float) -> MudSystem:

        return self.current_section(depth_ft).mud_system


    def section_description(self, depth_ft: float) -> str:

        return self.current_section(depth_ft).description


    def expected_section_days(self, depth_ft: float) -> float:

        return self.current_section(depth_ft).expected_section_days


    # ==========================================================
    # CASING LOOKUPS
    # ==============================================================

    def casing_size(self, depth_ft: float) -> float:

        return self.current_casing(depth_ft).casing.value


    def casing_label(self, depth_ft: float) -> str:

        return self.current_casing(depth_ft).casing.label


    def casing_grade(self, depth_ft: float) -> CasingGrade:

        return self.current_casing(depth_ft).grade


    def casing_weight(self, depth_ft: float) -> float:

        return self.current_casing(depth_ft).weight_lb_ft


    def casing_connection(self, depth_ft: float) -> str:

        return self.current_casing(depth_ft).connection


    def drift_id(self, depth_ft: float) -> float:

        return self.current_casing(depth_ft).drift_id_in


    def casing_shoe(self, depth_ft: float) -> float:

        return self.current_casing(depth_ft).setting_depth_ft


    def cement_top(self, depth_ft: float) -> float:

        return self.current_casing(depth_ft).cement_top_ft


    def annular_clearance(self, depth_ft: float) -> float:
        """
        Returns hole diameter minus casing OD.
        """

        casing = self.current_casing(depth_ft)

        return round(

            casing.hole.value - casing.casing.value,

            3

        )


    # ==========================================================
    # TRAJECTORY LOOKUPS
    # ==============================================================

    def inclination(self, depth_ft: float) -> float:

        return self.current_trajectory(depth_ft).inclination_end_deg


    def azimuth(self, depth_ft: float) -> float:

        return self.current_trajectory(depth_ft).azimuth_deg


    def dogleg(self, depth_ft: float) -> float:

        return self.current_trajectory(depth_ft).max_dogleg_deg100ft


    # ==========================================================
    # BOP
    # ==============================================================

    @property
    def bop(self) -> BOPConfiguration:

        return self.bop_configuration


    # ==========================================================
    # COMPLETION
    # ==============================================================

    @property
    def completion(self) -> CompletionConfiguration:

        return self.completion_configuration
    
        # ==========================================================
    # ENGINEERING VALIDATION
    # ==============================================================

    def validate_hole_program(self) -> bool:
        """
        Validate the hole program.
        """

        valid = True

        previous_bottom = 0.0

        for section in self.hole_program:

            if section.top_depth_ft != previous_bottom:

                print(
                    f"[ERROR] Hole program gap before "
                    f"{section.name}"
                )

                valid = False

            if section.bottom_depth_ft <= section.top_depth_ft:

                print(
                    f"[ERROR] Invalid interval in "
                    f"{section.name}"
                )

                valid = False

            previous_bottom = section.bottom_depth_ft

        if previous_bottom != self.total_depth_ft:

            print("[ERROR] Hole program does not reach TD")

            valid = False

        return valid


    # ==========================================================
    # CASING VALIDATION
    # ==============================================================

    def validate_casing_program(self) -> bool:
        """
        Validate casing geometry.
        """

        valid = True

        for casing in self.casing_program:

            clearance = casing.hole.value - casing.casing.value

            if clearance <= 0:

                print(

                    f"[ERROR] Negative clearance "

                    f"({casing.name})"

                )

                valid = False

            if casing.setting_depth_ft > self.total_depth_ft:

                print(

                    f"[ERROR] Casing beyond TD "

                    f"({casing.name})"

                )

                valid = False

        return valid


    # ==========================================================
    # CEMENT VALIDATION
    # ==============================================================

    def validate_cement_program(self) -> bool:

        valid = True

        for cement in self.cement_program:

            if cement.top_depth_ft >= cement.bottom_depth_ft:

                print(

                    f"[ERROR] Cement interval "

                    f"{cement.casing_name}"

                )

                valid = False

        return valid


    # ==========================================================
    # TRAJECTORY VALIDATION
    # ==============================================================

    def validate_trajectory(self) -> bool:

        valid = True

        previous = 0.0

        for section in self.trajectory_program:

            if section.md_from_ft != previous:

                print(

                    f"[ERROR] Trajectory gap "

                    f"{section.name}"

                )

                valid = False

            previous = section.md_to_ft

        if previous != self.total_depth_ft:

            print(

                "[ERROR] Trajectory does not reach TD"

            )

            valid = False

        return valid


    # ==========================================================
    # COMPLETION VALIDATION
    # ==============================================================

    def validate_completion(self) -> bool:

        completion = self.completion

        if completion.tubing.value >= completion.liner.value:

            print(

                "[ERROR] Tubing larger than liner"

            )

            return False

        return True


    # ==========================================================
    # COMPLETE VALIDATION
    # ==============================================================

    def validation_report(self) -> bool:
        """
        Run every engineering validation.
        """

        print()

        print("=" * 70)

        print("ENGINEERING VALIDATION")

        print("=" * 70)

        tests = {

            "Hole Program":

                self.validate_hole_program(),

            "Casing Program":

                self.validate_casing_program(),

            "Cement Program":

                self.validate_cement_program(),

            "Trajectory":

                self.validate_trajectory(),

            "Completion":

                self.validate_completion(),

        }

        passed = True

        print()

        for name, result in tests.items():

            status = "PASS" if result else "FAIL"

            print(f"{name:<25} {status}")

            passed &= result

        print()

        print("-" * 70)

        print(

            "OVERALL STATUS :",

            "PASSED" if passed else "FAILED"

        )

        print("-" * 70)

        print()

        return passed
    
        # ==========================================================
    # REPORTING ENGINE
    # ==============================================================

    def print_general_information(self):
        """
        Prints the basic well information.
        """

        print()

        print("=" * 70)
        print("GENERAL INFORMATION")
        print("=" * 70)

        print(f"Well Name          : {self.well_name}")
        print(f"Operator           : {self.operator}")
        print(f"Country            : {self.country}")
        print(f"Field              : {self.field}")
        print(f"Field Type         : {self.field_type.value}")
        print(f"Well Type          : {self.well_type.value}")
        print(f"Status             : {self.status.value}")
        print(f"Rig                : {self.rig_name}")
        print(f"Water Depth (ft)   : {self.water_depth_ft}")
        print(f"Total Depth (ft)   : {self.total_depth_ft}")
        print(f"KB Elevation (ft)  : {self.kb_elevation_ft}")
        print(f"Latitude           : {self.latitude}")
        print(f"Longitude          : {self.longitude}")


    # ==========================================================
    # HOLE PROGRAM REPORT
    # ==============================================================

    def print_hole_program(self):

        print()

        print("=" * 70)
        print("HOLE PROGRAM")
        print("=" * 70)

        for section in self.hole_program:

            print(
                f"{section.name:<15}"
                f"{section.top_depth_ft:>7.0f}"
                f"{section.bottom_depth_ft:>8.0f}"
                f"   {section.hole.label:<10}"
                f"{section.bit.label:<10}"
                f"{section.mud_system.value:<24}"
                f"{section.expected_section_days:>6.1f} days"
            )


    # ==========================================================
    # CASING REPORT
    # ==============================================================

    def print_casing_program(self):

        print()

        print("=" * 70)
        print("CASING PROGRAM")
        print("=" * 70)

        for casing in self.casing_program:

            print(
                f"{casing.name:<20}"
                f"{casing.casing.label:<10}"
                f"{casing.hole.label:<10}"
                f"{casing.setting_depth_ft:>8.0f}"
                f"   {casing.grade.value:<6}"
                f"{casing.weight_lb_ft:>7.1f}"
            )


    # ==========================================================
    # CEMENT REPORT
    # ==============================================================

    def print_cement_program(self):

        print()

        print("=" * 70)
        print("CEMENT PROGRAM")
        print("=" * 70)

        for cement in self.cement_program:

            print(
                f"{cement.casing_name:<20}"
                f"{cement.slurry_type:<24}"
                f"{cement.top_depth_ft:>7.0f}"
                f"{cement.bottom_depth_ft:>8.0f}"
            )


    # ==========================================================
    # TRAJECTORY REPORT
    # ==============================================================

    def print_trajectory(self):

        print()

        print("=" * 70)
        print("TRAJECTORY")
        print("=" * 70)

        for section in self.trajectory_program:

            print(
                f"{section.name:<15}"
                f"{section.md_from_ft:>7.0f}"
                f"{section.md_to_ft:>8.0f}"
                f"   Inc "
                f"{section.inclination_start_deg:>5.1f}"
                f" -> "
                f"{section.inclination_end_deg:>5.1f}"
                f"   Azi {section.azimuth_deg:>6.1f}"
            )


    # ==========================================================
    # BOP REPORT
    # ==============================================================

    def print_bop(self):

        bop = self.bop

        print()

        print("=" * 70)
        print("BOP CONFIGURATION")
        print("=" * 70)

        print(f"Pressure Rating : {bop.pressure_rating_psi:,} psi")
        print(f"Annulars        : {bop.annular_preventers}")
        print(f"Ram Preventers  : {bop.ram_preventers}")
        print(f"Shear Ram       : {bop.shear_ram}")
        print(f"Diverter        : {bop.diverter}")


    # ==========================================================
    # COMPLETION REPORT
    # ==============================================================

    def print_completion(self):

        completion = self.completion

        print()

        print("=" * 70)
        print("COMPLETION")
        print("=" * 70)

        print(f"Completion Type : {completion.completion_type.value}")
        print(f"Tubing          : {completion.tubing}")
        print(f"Liner           : {completion.liner}")
        print(f"Packer          : {completion.packer}")
        print(f"Sand Control    : {completion.sand_control}")


    # ==========================================================
    # COMPLETE ENGINEERING REPORT
    # ==============================================================

    def engineering_report(self):
        """
        Prints the complete engineering report.
        """

        self.print_general_information()

        self.print_hole_program()

        self.print_casing_program()

        self.print_cement_program()

        self.print_trajectory()

        self.print_bop()

        self.print_completion()

        self.validation_report()

# ==============================================================
# MAIN TEST PROGRAM
# ==============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("WELL DESIGN LIBRARY")
    print("Version 1.3")
    print("=" * 70)

    # ----------------------------------------------------------
    # Create Engineering Model
    # ----------------------------------------------------------

    well = WellDesign()

    print()
    print("Library initialized successfully.")
    print()

    # ----------------------------------------------------------
    # General Information
    # ----------------------------------------------------------

    well.print_general_information()

    # ----------------------------------------------------------
    # Hole Program
    # ----------------------------------------------------------

    well.print_hole_program()

    # ----------------------------------------------------------
    # Casing Program
    # ----------------------------------------------------------

    well.print_casing_program()

    # ----------------------------------------------------------
    # Cement Program
    # ----------------------------------------------------------

    well.print_cement_program()

    # ----------------------------------------------------------
    # Trajectory
    # ----------------------------------------------------------

    well.print_trajectory()

    # ----------------------------------------------------------
    # BOP
    # ----------------------------------------------------------

    well.print_bop()

    # ----------------------------------------------------------
    # Completion
    # ----------------------------------------------------------

    well.print_completion()

    # ----------------------------------------------------------
    # Lookup Examples
    # ----------------------------------------------------------

    print()
    print("=" * 70)
    print("ENGINEERING LOOKUP EXAMPLES")
    print("=" * 70)

    test_depths = [

        100,
        1200,
        5000,
        12000,
        19500

    ]

    for depth in test_depths:

        print()
        print(f"Depth : {depth:,.0f} ft")
        print("-" * 40)

        print(f"Section              : {well.section_name(depth)}")
        print(f"Hole                 : {well.hole_label(depth)}")
        print(f"Bit                  : {well.bit_label(depth)}")
        print(f"Mud System           : {well.mud_system(depth).value}")
        print(f"Casing              : {well.casing_label(depth)}")
        print(f"Casing Grade        : {well.casing_grade(depth).value}")
        print(f"Connection          : {well.casing_connection(depth)}")
        print(f"Drift ID            : {well.drift_id(depth):.3f} in")
        print(f"Annular Clearance   : {well.annular_clearance(depth):.3f} in")
        print(f"Inclination         : {well.inclination(depth):.1f}°")
        print(f"Azimuth             : {well.azimuth(depth):.1f}°")
        print(f"Dogleg Severity     : {well.dogleg(depth):.1f}°/100 ft")
        print(f"Expected Days       : {well.expected_section_days(depth):.1f}")

    # ----------------------------------------------------------
    # Validation
    # ----------------------------------------------------------

    print()

    passed = well.validation_report()

    # ----------------------------------------------------------
    # Complete Engineering Report
    # ----------------------------------------------------------

    print()
    print("=" * 70)
    print("COMPLETE ENGINEERING REPORT")
    print("=" * 70)

    well.engineering_report()

    # ----------------------------------------------------------
    # Final Status
    # ----------------------------------------------------------

    print()

    print("=" * 70)

    if passed:

        print("STATUS : WELL DESIGN MODEL PASSED")

    else:

        print("STATUS : WELL DESIGN MODEL FAILED")

    print("=" * 70)

    print()

    print("Version 1.3 Test Completed Successfully.")