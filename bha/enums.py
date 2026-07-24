"""
========================================================================
BHA Engineering Suite v2.0

enums.py

Common enumerations used throughout the package.

Author : Anibal Ceballos
========================================================================
"""

from enum import Enum


# ======================================================================
# COMPONENT TYPES
# ======================================================================

class ComponentType(str, Enum):
    BIT = "Bit"
    DRILL_COLLAR = "Drill Collar"
    HWDP = "Heavy Weight Drill Pipe"
    DRILL_PIPE = "Drill Pipe"
    STABILIZER = "Stabilizer"
    MUD_MOTOR = "Mud Motor"
    RSS = "Rotary Steerable System"
    MWD = "Measurement While Drilling"
    LWD = "Logging While Drilling"
    JAR = "Jar"
    SHOCK_SUB = "Shock Sub"
    FLOAT_SUB = "Float Sub"
    REAMER = "Reamer"
    CROSSOVER = "Crossover"


# ======================================================================
# STEEL GRADE
# ======================================================================

class SteelGrade(str, Enum):
    E75 = "E-75"
    X95 = "X-95"
    G105 = "G-105"
    S135 = "S-135"


# ======================================================================
# CONNECTION TYPE
# ======================================================================

class ConnectionType(str, Enum):
    API_REG = "API REG"
    API_IF = "API IF"
    NC38 = "NC38"
    NC46 = "NC46"
    NC50 = "NC50"
    XT57 = "XT57"


# ======================================================================
# STEERING
# ======================================================================

class SteeringType(str, Enum):
    NONE = "None"
    SLIDE = "Slide"
    ROTARY = "Rotary"
    HYBRID = "Hybrid"


# ======================================================================
# WELL PROFILE
# ======================================================================

class BHAProfile(str, Enum):
    VERTICAL = "Vertical"
    BUILD = "Build"
    HOLD = "Hold"
    DROP = "Drop"
    HORIZONTAL = "Horizontal"


# ======================================================================
# HOLE SECTION
# ======================================================================

class HoleSection(str, Enum):
    SURFACE = "Surface"
    INTERMEDIATE = "Intermediate"
    PRODUCTION = "Production"
    LINER = "Liner"


# ======================================================================
# BIT TYPE
# ======================================================================

class BitType(str, Enum):
    PDC = "PDC"
    TRICONE = "Tricone"
    HYBRID = "Hybrid"
    IMPREG = "Impreg"


# ======================================================================
# BEARING TYPE
# ======================================================================

class BearingType(str, Enum):
    SEALED = "Sealed"
    OPEN = "Open"
    NONE = "None"