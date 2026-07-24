"""
===========================================================================
assembly.py

Bottom Hole Assembly object

Core object representing a complete Bottom Hole Assembly.

Author : OpenAI + Anibal Ceballos
Project : Guyana Offshore Drilling Analytics
===========================================================================
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .constants import (
    DEFAULT_BUOYANCY_FACTOR,
    DEFAULT_OPEN_HOLE_FRICTION,
    DEFAULT_CASING_FRICTION,
)


from .components import BHAComponent
from .enums import (
    ComponentType,
    HoleSection,
)


@dataclass
class BottomHoleAssembly:
    """
    Complete Bottom Hole Assembly.

    A BHA is composed of multiple components ordered from
    bit to drill pipe.

    The class stores the entire assembly and exposes
    engineering properties used by the rest of the package.
    """

    name: str

    section: HoleSection

    hole_size_in: float

    components: list[BHAComponent] = field(default_factory=list)

###############################################################################
# Hydraulics
###############################################################################

    flow_rate_gpm: float = 0.0

    pump_pressure_psi: float = 0.0

    bit_pressure_loss_psi: float = 0.0

    nozzle_area_in2: float = 0.0

    mud_weight_ppg: float = 10.
    
###############################################################################
# Torque & Drag
###############################################################################

    open_hole_friction: float = DEFAULT_OPEN_HOLE_FRICTION

    casing_friction: float = DEFAULT_CASING_FRICTION

    buoyancy_factor: float = DEFAULT_BUOYANCY_FACTOR

###############################################################################
# Survey
###############################################################################

    md1_ft: float = 0.0

    md2_ft: float = 100.0

    tvd1_ft: float = 0.0

    northing1_ft: float = 0.0

    easting1_ft: float = 0.0

###############################################################################
# Well Geometry
###############################################################################

    hole_inclination_deg: float = 0.0

    friction_factor: float = 0.25
# ---------------------------------------------------------
# Automatically detected major tools
# ---------------------------------------------------------

    bit: Optional[BHAComponent] = None

    motor: Optional[BHAComponent] = None

    rss: Optional[BHAComponent] = None

    mwd: Optional[BHAComponent] = None

    lwd: Optional[BHAComponent] = None

    near_bit_stabilizer: Optional[BHAComponent] = None

    string_stabilizers: list[BHAComponent] = field(default_factory=list)

    # =========================================================
    # COMPONENT MANAGEMENT
    # =========================================================

    def add_component(
        self,
        component: BHAComponent
    ) -> None:
        """
        Add a component to the BHA.

        Components are stored in bit-to-surface order.
        """

        self.components.append(component)
        self._refresh_components()

    # ---------------------------------------------------------

    def insert_component(
        self,
        index: int,
        component: BHAComponent
    ) -> None:
        """
        Insert a component at a specific position.
        """

        self.components.insert(index, component)
        self._refresh_components()

    # ---------------------------------------------------------

    def remove_component(
        self,
        component_name: str
    ) -> bool:
        """
        Remove a component by name.

        Returns
        -------
        bool
            True if removed.
        """

        for component in self.components:

            if component.name == component_name:

                self.components.remove(component)

                self._refresh_components()

                return True

        return False

    # ---------------------------------------------------------

    def clear(self) -> None:
        """
        Remove every component from the assembly.
        """

        self.components.clear()

        self._refresh_components()

    # =========================================================
    # INTERNAL UPDATE
    # =========================================================

    def _refresh_components(self) -> None:
        """
        Automatically detect the main tools after
        every modification.
        """

        self.bit = None
        self.motor = None
        self.rss = None
        self.mwd = None
        self.lwd = None
        self.near_bit_stabilizer = None
        self.string_stabilizers.clear()

        for component in self.components:

            match component.component_type:

                case ComponentType.BIT:

                    self.bit = component

                case ComponentType.MOTOR:

                    self.motor = component

                case ComponentType.RSS:

                    self.rss = component

                case ComponentType.MWD:

                    self.mwd = component

                case ComponentType.LWD:

                    self.lwd = component

                case ComponentType.STABILIZER:

                    if self.near_bit_stabilizer is None:

                        self.near_bit_stabilizer = component

                    else:

                        self.string_stabilizers.append(component)

    # =========================================================
    # SIMPLE ACCESSORS
    # =========================================================

    @property
    def number_of_components(self) -> int:
        """
        Total number of BHA components.
        """

        return len(self.components)

    # ---------------------------------------------------------

    @property
    def has_motor(self) -> bool:

        return self.motor is not None

    # ---------------------------------------------------------

    @property
    def has_rss(self) -> bool:

        return self.rss is not None

    # ---------------------------------------------------------

    @property
    def has_mwd(self) -> bool:

        return self.mwd is not None

    # ---------------------------------------------------------

    @property
    def has_lwd(self) -> bool:

        return self.lwd is not None

    # ---------------------------------------------------------

    @property
    def has_bit(self) -> bool:

        return self.bit is not None
    
    # =========================================================
    # ENGINEERING PROPERTIES
    # =========================================================

    @property
    def total_length(self) -> float:
        """
        Total BHA length (ft).
        """

        return sum(
            component.length_ft
            for component in self.components
        )

    # ---------------------------------------------------------

    @property
    def total_weight(self) -> float:
        """
        Total BHA weight (lb).
        """

        return sum(
            component.weight_lb
            for component in self.components
        )

    # ---------------------------------------------------------

    @property
    def drill_collar_weight(self) -> float:
        """
        Total Drill Collar weight.
        """

        return sum(

            component.weight_lb

            for component in self.components

            if component.component_type == ComponentType.DRILL_COLLAR

        )

    # ---------------------------------------------------------

    @property
    def drill_collar_length(self) -> float:
        """
        Total Drill Collar length.
        """

        return sum(

            component.length_ft

            for component in self.components

            if component.component_type == ComponentType.DRILL_COLLAR

        )

    # ---------------------------------------------------------

    @property
    def hwdp_weight(self) -> float:
        """
        Total Heavy Weight Drill Pipe weight.
        """

        return sum(

            component.weight_lb

            for component in self.components

            if component.component_type == ComponentType.HWDP

        )

    # ---------------------------------------------------------

    @property
    def hwdp_length(self) -> float:
        """
        Total Heavy Weight Drill Pipe length.
        """

        return sum(

            component.length_ft

            for component in self.components

            if component.component_type == ComponentType.HWDP

        )

    # ---------------------------------------------------------

    @property
    def drillpipe_weight(self) -> float:
        """
        Total Drill Pipe weight.
        """

        return sum(

            component.weight_lb

            for component in self.components

            if component.component_type == ComponentType.DRILL_PIPE

        )

    # ---------------------------------------------------------

    @property
    def drillpipe_length(self) -> float:
        """
        Total Drill Pipe length.
        """

        return sum(

            component.length_ft

            for component in self.components

            if component.component_type == ComponentType.DRILL_PIPE

        )

    # ---------------------------------------------------------

    @property
    def total_stabilizers(self) -> int:
        """
        Number of stabilizers.
        """

        return sum(

            1

            for component in self.components

            if component.component_type == ComponentType.STABILIZER

        )

    # ---------------------------------------------------------

    @property
    def average_component_weight(self) -> float:
        """
        Average component weight.
        """

        if not self.components:
            return 0.0

        return self.total_weight / len(self.components)

    # ---------------------------------------------------------

    @property
    def average_component_length(self) -> float:
        """
        Average component length.
        """

        if not self.components:
            return 0.0

        return self.total_length / len(self.components)
    
    # =========================================================
    # ENGINEERING SUMMARY
    # =========================================================

    @property
    def center_of_length(self) -> float:
        """
        Mid-point of the BHA measured from the bit.

        Returns
        -------
        float
            Feet from bit.
        """

        return self.total_length / 2.0

    # ---------------------------------------------------------

    @property
    def center_of_gravity(self) -> float:
        """
        Center of gravity measured from the bit.

        Assumes each component's weight acts at its midpoint.
        """

        if not self.components:
            return 0.0

        moment = 0.0
        position = 0.0

        for component in self.components:

            midpoint = position + component.length_ft / 2.0

            moment += midpoint * component.weight_lb

            position += component.length_ft

        if self.total_weight == 0:
            return 0.0

        return moment / self.total_weight

    # ---------------------------------------------------------

    @property
    def component_types(self) -> list[str]:
        """
        List of unique component types.
        """

        return sorted({

            component.component_type.name

            for component in self.components

        })

    # ---------------------------------------------------------

    @property
    def contains_directional_tools(self) -> bool:
        """
        True if BHA contains Motor or RSS.
        """

        return self.has_motor or self.has_rss

    # ---------------------------------------------------------

    @property
    def is_rotary_bha(self) -> bool:
        """
        Rotary BHA without directional tools.
        """

        return not self.contains_directional_tools

    # ---------------------------------------------------------

    @property
    def is_directional_bha(self) -> bool:
        """
        Directional drilling assembly.
        """

        return self.contains_directional_tools

    # ---------------------------------------------------------

    @property
    def tool_count(self) -> dict[str, int]:
        """
        Count components by type.
        """

        counts = {}

        for component in self.components:

            key = component.component_type.name

            counts[key] = counts.get(key, 0) + 1

        return counts

    # ---------------------------------------------------------

    def component_summary(self) -> list[dict]:
        """
        Return a list describing every component.

        Useful for Power BI datasets.
        """

        summary = []

        position = 0.0

        for component in self.components:

            summary.append({

                "name": component.name,

                "type": component.component_type.name,

                "od_in": component.od,

                "length_ft": component.length_ft,

                "weight_lb": component.weight_lb,

                "top_depth_ft": position,

                "bottom_depth_ft": position + component.length_ft

            })

            position += component.length_ft

        return summary

    # ---------------------------------------------------------

    def describe(self) -> str:
        """
        Human-readable BHA description.
        """

        return (

            f"{self.name} | "

            f"{self.section.value} | "

            f"Hole {self.hole_size_in:.2f}\" | "

            f"{self.number_of_components} components | "

            f"{self.total_length:.1f} ft | "

            f"{self.total_weight:,.0f} lb"

        )
    
    # =========================================================
    # VALIDATION
    # =========================================================

    def validate(self) -> list[str]:
        """
        Validate the BHA.

        Returns
        -------
        list[str]
            List of validation errors.
        """

        errors = []

        # -----------------------------------------------------
        # Empty BHA
        # -----------------------------------------------------

        if not self.components:

            errors.append("Assembly contains no components.")

            return errors

        # -----------------------------------------------------
        # Bit
        # -----------------------------------------------------

        if self.bit is None:

            errors.append("No drill bit found.")

        # -----------------------------------------------------
        # Hole Size
        # -----------------------------------------------------

        if self.hole_size_in <= 0:

            errors.append("Invalid hole size.")

        # -----------------------------------------------------
        # Component dimensions
        # -----------------------------------------------------

        for component in self.components:

            if component.od <= 0:

                errors.append(
                    f"{component.name}: invalid outside diameter."
                )

            if component.length_ft <= 0:

                errors.append(
                    f"{component.name}: invalid length."
                )

            if component.weight_lb <= 0:

                errors.append(
                    f"{component.name}: invalid weight."
                )

        # -----------------------------------------------------
        # Duplicate unique tools
        # -----------------------------------------------------

        unique_tools = {

            ComponentType.BIT: 0,

            ComponentType.MOTOR: 0,

            ComponentType.RSS: 0,

            ComponentType.MWD: 0,

            ComponentType.LWD: 0,

        }

        for component in self.components:

            if component.component_type in unique_tools:

                unique_tools[
                    component.component_type
                ] += 1

        for tool, quantity in unique_tools.items():

            if quantity > 1:

                errors.append(
                    f"Multiple {tool.name} tools detected."
                )

        # -----------------------------------------------------
        # RSS and Motor simultaneously
        # -----------------------------------------------------

        if self.has_motor and self.has_rss:

            errors.append(
                "Motor and RSS should not exist in the same BHA."
            )

        # -----------------------------------------------------
        # Directional drilling
        # -----------------------------------------------------

        if self.is_directional_bha:

            if not self.has_mwd:

                errors.append(
                    "Directional BHA requires an MWD tool."
                )

        # -----------------------------------------------------
        # Component OD vs Hole Size
        # -----------------------------------------------------

        for component in self.components:

            if component.od > self.hole_size_in:

                errors.append(

                    f"{component.name} OD "

                    f"({component.od:.2f}\") "

                    f"exceeds hole size "

                    f"({self.hole_size_in:.2f}\")."

                )

        return errors

    # ---------------------------------------------------------

    @property
    def is_valid(self) -> bool:
        """
        True if no validation errors exist.
        """

        return len(self.validate()) == 0

    # ---------------------------------------------------------

    def validation_report(self) -> None:
        """
        Print validation results.
        """

        print("=" * 70)
        print("BHA VALIDATION")
        print("=" * 70)

        errors = self.validate()

        if not errors:

            print("STATUS : VALID")

        else:

            print("STATUS : INVALID")

            print()

            for error in errors:

                print(f"- {error}")

        print("=" * 70)

    # =========================================================
    # SERIALIZATION
    # =========================================================

    def to_dict(self) -> dict:
        """
        Convert the entire BHA into a dictionary.

        Suitable for JSON serialization, APIs,
        Power BI ingestion and database storage.
        """

        return {

            "name": self.name,

            "section": self.section.value,

            "hole_size_in": self.hole_size_in,

            "total_components": self.number_of_components,

            "total_length_ft": self.total_length,

            "total_weight_lb": self.total_weight,

            "center_of_gravity_ft": self.center_of_gravity,

            "is_valid": self.is_valid,

            "components": [

                {

                    "name": c.name,

                    "type": c.component_type.name,

                    "od_in": c.od,

                    "length_ft": c.length_ft,

                    "weight_lb": c.weight_lb

                }

                for c in self.components

            ]

        }

    # ---------------------------------------------------------

    @classmethod
    def from_dict(
        cls,
        data: dict
    ) -> "BottomHoleAssembly":
        """
        Create a BottomHoleAssembly from a dictionary.

        Components must be added separately because
        different subclasses of BHAComponent may exist.
        """

        section = HoleSection(data["section"])

        bha = cls(

            name=data["name"],

            section=section,

            hole_size_in=data["hole_size_in"]

        )

        return bha

    # ---------------------------------------------------------

    def component_dataframe(self) -> list[dict]:
        """
        Return a tabular representation of components.

        Can be directly converted into a pandas DataFrame.

        Example
        -------
        pd.DataFrame(bha.component_dataframe())
        """

        rows = []

        cumulative = 0.0

        for index, component in enumerate(self.components, start=1):

            rows.append({

                "sequence": index,

                "name": component.name,

                "type": component.component_type.name,

                "outside_diameter_in": component.od,

                "length_ft": component.length_ft,

                "weight_lb": component.weight_lb,

                "top_depth_ft": cumulative,

                "bottom_depth_ft": cumulative + component.length_ft

            })

            cumulative += component.length_ft

        return rows

    # ---------------------------------------------------------

    def summary_dict(self) -> dict:
        """
        Compact engineering summary.

        Useful for dashboards and reports.
        """

        return {

            "name": self.name,

            "section": self.section.value,

            "hole_size": self.hole_size_in,

            "components": self.number_of_components,

            "length_ft": self.total_length,

            "weight_lb": self.total_weight,

            "drill_collar_weight_lb": self.drill_collar_weight,

            "hwdp_weight_lb": self.hwdp_weight,

            "drillpipe_weight_lb": self.drillpipe_weight,

            "has_motor": self.has_motor,

            "has_rss": self.has_rss,

            "has_mwd": self.has_mwd,

            "has_lwd": self.has_lwd,

            "valid": self.is_valid

        }

    # ---------------------------------------------------------

    def __len__(self) -> int:
        """
        Number of components.
        """

        return self.number_of_components

    # ---------------------------------------------------------

    def __iter__(self):
        """
        Iterate over BHA components.
        """

        return iter(self.components)

    # ---------------------------------------------------------

    def __contains__(
        self,
        component: BHAComponent
    ) -> bool:
        """
        Check if a component exists in the assembly.
        """

        return component in self.components

    # ---------------------------------------------------------

    def __str__(self) -> str:

        return self.describe()

    # ---------------------------------------------------------

    def __repr__(self) -> str:

        return (

            f"BottomHoleAssembly("

            f"name='{self.name}', "

            f"section='{self.section.value}', "

            f"hole_size={self.hole_size_in}, "

            f"components={self.number_of_components}"

            f")"

        )

    # =========================================================
    # ENGINEERING UTILITIES
    # =========================================================

    def components_by_type(
        self,
        component_type: ComponentType
    ) -> list[BHAComponent]:
        """
        Return all components of a given type.
        """

        return [

            component

            for component in self.components

            if component.component_type == component_type

        ]

    # ---------------------------------------------------------

    def first_component(
        self,
        component_type: ComponentType
    ) -> BHAComponent | None:
        """
        Return the first component of a given type.
        """

        for component in self.components:

            if component.component_type == component_type:

                return component

        return None

    # ---------------------------------------------------------

    def last_component(
        self,
        component_type: ComponentType
    ) -> BHAComponent | None:
        """
        Return the last component of a given type.
        """

        for component in reversed(self.components):

            if component.component_type == component_type:

                return component

        return None

    # ---------------------------------------------------------

    def component_exists(
        self,
        component_type: ComponentType
    ) -> bool:
        """
        Check if a component type exists.
        """

        return any(

            component.component_type == component_type

            for component in self.components

        )

    # ---------------------------------------------------------

    def count(
        self,
        component_type: ComponentType
    ) -> int:
        """
        Count components of a given type.
        """

        return sum(

            1

            for component in self.components

            if component.component_type == component_type

        )

    # ---------------------------------------------------------

    def depth_to_component(
        self,
        component_name: str
    ) -> float | None:
        """
        Return the depth from the bit to the top
        of the requested component.
        """

        depth = 0.0

        for component in self.components:

            if component.name == component_name:

                return depth

            depth += component.length_ft

        return None

    # ---------------------------------------------------------

    def component_at_depth(
        self,
        depth_ft: float
    ) -> BHAComponent | None:
        """
        Return the component occupying
        a given measured depth.
        """

        current = 0.0

        for component in self.components:

            top = current
            bottom = current + component.length_ft

            if top <= depth_ft < bottom:

                return component

            current = bottom

        return None

    # ---------------------------------------------------------

    def bit_to_surface_profile(self) -> list[tuple]:
        """
        Build the complete BHA profile.

        Returns
        -------
        list

        (Component Name,
         Top Depth,
         Bottom Depth)
        """

        profile = []

        depth = 0.0

        for component in self.components:

            profile.append(

                (

                    component.name,

                    depth,

                    depth + component.length_ft

                )

            )

            depth += component.length_ft

        return profile

    # ---------------------------------------------------------

    def total_internal_volume(self) -> float:
        """
        Total internal volume.

        Placeholder for future hydraulic model.
        """

        volume = 0.0

        for component in self.components:

            if hasattr(component, "internal_volume"):

                volume += component.internal_volume

        return volume

    # ---------------------------------------------------------

    def total_flow_area(self) -> float:
        """
        Total flow area.

        Reserved for hydraulic calculations.
        """

        area = 0.0

        for component in self.components:

            if hasattr(component, "flow_area"):

                area += component.flow_area

        return area

    # ---------------------------------------------------------

    def clone(self) -> "BottomHoleAssembly":
        """
        Deep copy of the assembly.
        """

        from copy import deepcopy

        return deepcopy(self)
    
    # =========================================================
    # SEARCH UTILITIES
    # =========================================================

    def find(
        self,
        text: str
    ) -> list[BHAComponent]:
        """
        Search components by partial name.
        """

        text = text.lower()

        return [

            component

            for component in self.components

            if text in component.name.lower()

        ]

    # ---------------------------------------------------------

    def sort_components(
        self,
        reverse: bool = False
    ) -> None:
        """
        Sort components by measured depth.

        Normally they are already stored in
        bit-to-surface order.
        """

        self.components.sort(

            key=lambda component: component.length_ft,

            reverse=reverse

        )

    # ---------------------------------------------------------

    def reverse(self) -> None:
        """
        Reverse assembly order.
        """

        self.components.reverse()

        self._refresh_components()

    # =========================================================
    # PYTHON SPECIAL METHODS
    # =========================================================

    def __getitem__(
        self,
        index: int
    ) -> BHAComponent:

        return self.components[index]

    # ---------------------------------------------------------

    def __bool__(self) -> bool:

        return bool(self.components)

    # ---------------------------------------------------------

    def __eq__(
        self,
        other: object
    ) -> bool:

        if not isinstance(other, BottomHoleAssembly):

            return False

        return (

            self.name == other.name

            and

            self.section == other.section

            and

            self.hole_size_in == other.hole_size_in

            and

            self.components == other.components

        )

    # ---------------------------------------------------------

    def __hash__(self) -> int:

        return hash(

            (

                self.name,

                self.section,

                self.hole_size_in

            )

        )

    # =========================================================
    # REPORTING
    # =========================================================

    def print_summary(self) -> None:
        """
        Print a concise engineering summary.
        """

        print("=" * 70)

        print(self.name)

        print("=" * 70)

        print(f"Section              : {self.section.value}")

        print(f"Hole Size            : {self.hole_size_in:.2f}\"")

        print(f"Components           : {self.number_of_components}")

        print(f"Length               : {self.total_length:.1f} ft")

        print(f"Weight               : {self.total_weight:,.0f} lb")

        print(f"Center of Gravity    : {self.center_of_gravity:.1f} ft")

        print(f"Valid                : {self.is_valid}")

        print("=" * 70)

    # ---------------------------------------------------------

    def print_components(self) -> None:
        """
        Print every component.
        """

        print("=" * 90)

        print("COMPONENT LIST")

        print("=" * 90)

        depth = 0.0

        for component in self.components:

            print(

                f"{depth:8.1f} - "

                f"{depth + component.length_ft:8.1f} ft   "

                f"{component.name:35}"

                f"{component.weight_lb:8.0f} lb"

            )

            depth += component.length_ft

        print("=" * 90)

    # ---------------------------------------------------------

    def print_report(self) -> None:
        """
        Complete engineering report.
        """

        self.print_summary()

        print()

        self.validation_report()

        print()

        self.print_components()

