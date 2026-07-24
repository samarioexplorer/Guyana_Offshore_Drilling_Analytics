"""
========================================================================
BHA Engineering Suite v2.1

constants.py

Global engineering constants used throughout the BHA Engineering Suite.

Author : Anibal Ceballos
========================================================================
"""

from __future__ import annotations

###############################################################################
# UNIT CONVERSIONS
###############################################################################

INCHES_PER_FOOT = 12.0

FEET_PER_METER = 3.28084

METERS_PER_FOOT = 0.3048

POUNDS_PER_KILOGRAM = 2.20462

KILOGRAMS_PER_POUND = 0.45359237

GALLONS_PER_BARREL = 42.0

###############################################################################
# PHYSICAL CONSTANTS
###############################################################################

GRAVITY_FTPS2 = 32.174

STANDARD_GRAVITY = 9.80665

PI = 3.141592653589793

###############################################################################
# STEEL PROPERTIES
###############################################################################

STEEL_DENSITY_LBFT3 = 490.0

STEEL_DENSITY_GCM3 = 7.85

STEEL_YOUNGS_MODULUS_PSI = 30_000_000

STEEL_POISSON_RATIO = 0.30

###############################################################################
# DRILLING FLUID DEFAULTS
###############################################################################

DEFAULT_MUD_WEIGHT_PPG = 10.0

DEFAULT_BUOYANCY_FACTOR = 0.85

DEFAULT_FLOW_RATE_GPM = 600.0

DEFAULT_PRESSURE_LOSS_PSI = 1500.0

###############################################################################
# HYDRAULICS
###############################################################################

HYDRAULIC_HP_CONSTANT = 1714.0

JET_VELOCITY_CONSTANT = 0.3208

BIT_HYDRAULIC_EFFICIENCY = 0.65

###############################################################################
# WOB CONSTANTS
###############################################################################

# Fraction of drill collar weight available as usable WOB
COLLAR_WOB_FACTOR = 0.85

# Recommended WOB by hole size
VERTICAL_WOB_LB = 60000.0
BUILD_SECTION_WOB_LB = 45000.0
HORIZONTAL_WOB_LB = 30000.0
SMALL_HOLE_WOB_LB = 20000.0

# Utilization limits
WOB_STATUS_LIMIT_LOW = 0.60
WOB_STATUS_LIMIT_HIGH = 0.90

# Engineering warning
MAX_WOB_UTILIZATION = 0.85

###############################################################################
# BUCKLING
###############################################################################

LOW_BUCKLING_RATIO = 0.60

MODERATE_BUCKLING_RATIO = 0.85

###############################################################################
# STIFFNESS
###############################################################################

MINIMUM_STIFFNESS_INDEX = 1200.0

###############################################################################
# ENGINEERING SCORE
###############################################################################

INITIAL_ENGINEERING_SCORE = 100.0

PENALTY_HIGH_WOB = 30.0

PENALTY_LOW_STIFFNESS = 15.0

PENALTY_NO_MWD = 10.0

PENALTY_NO_BIT = 20.0

###############################################################################
# VIBRATION LIMITS
###############################################################################

MAX_LATERAL_ACCELERATION_G = 20.0

MAX_AXIAL_ACCELERATION_G = 15.0

MAX_TORSIONAL_OSCILLATION_PERCENT = 30.0

###############################################################################
# TORQUE & DRAG
###############################################################################

DEFAULT_FRICTION_FACTOR_CASING = 0.20

DEFAULT_FRICTION_FACTOR_OPEN_HOLE = 0.30

###############################################################################
# RSS
###############################################################################

MAX_BUILD_RATE_DEG_PER100FT = 12.0

###############################################################################
# MWD/LWD
###############################################################################

DEFAULT_SURVEY_INTERVAL_FT = 90.0

###############################################################################
# POWER BI
###############################################################################

DEFAULT_DECIMAL_PRECISION = 2

###############################################################################
# NUMERICAL TOLERANCES
###############################################################################

FLOAT_TOLERANCE = 1e-9

###############################################################################
# DATABASE
###############################################################################

DEFAULT_MANUFACTURER = "Generic"

DEFAULT_MODEL = ""

DEFAULT_SERIAL = ""

###############################################################################
# BUCKLING CONSTANTS
###############################################################################

YOUNGS_MODULUS_STEEL_PSI = 30_000_000

GRAVITY_FTPS2 = 32.174

DEFAULT_HOLE_INCLINATION = 0.0

DEFAULT_FRICTION_FACTOR = 0.25

SINUSOIDAL_WARNING = 0.80

HELICAL_WARNING = 1.00

LOW_BUCKLING_RATIO = 0.60

MODERATE_BUCKLING_RATIO = 0.85

###############################################################################
# Torque & Drag
###############################################################################

DEFAULT_OPEN_HOLE_FRICTION = 0.30

DEFAULT_CASING_FRICTION = 0.20

DEFAULT_BUOYANCY_FACTOR = 0.85

MAX_SAFE_TORQUE_FTLB = 35000

MAX_SAFE_DRAG_LB = 120000

MAX_SAFE_SIDE_FORCE = 25000