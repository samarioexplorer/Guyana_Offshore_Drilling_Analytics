"""
===========================================================================
library.py

BHA Library Manager

Stores standard BHA templates and provides engineering utilities.

Author : OpenAI + Anibal Ceballos
Project : Guyana Offshore Drilling Analytics
===========================================================================
"""

from __future__ import annotations

from typing import Dict, List

from .components import BHAComponent

from .enums import ComponentType


class BHALibrary:
    """
    Stores and manages BHA templates.
    """

    def __init__(self):

        self.bhas: List[BHAComponent] = []

    # ------------------------------------------------------------------

    def add_bha(
        self,
        bha: BHAComponent
    ) -> None:

        self.bhas.append(bha)

    # ------------------------------------------------------------------

    def remove_bha(
        self,
        name: str
    ) -> bool:

        for bha in self.bhas:

            if bha.name == name:

                self.bhas.remove(bha)

                return True

        return False

    # ------------------------------------------------------------------

    def list_bhas(self) -> List[str]:

        return [
            bha.name
            for bha in self.bhas
        ]

    # ------------------------------------------------------------------

    def get_bha(
        self,
        name: str
    ) -> BHAComponent | None:

        for bha in self.bhas:

            if bha.name == name:
                return bha

        return None

    # ------------------------------------------------------------------

    def find_by_hole_size(
        self,
        hole_size: float
    ) -> List[BHAComponent]:

        return [

            bha

            for bha in self.bhas

            if abs(
                bha.hole_size_in - hole_size
            ) < 0.05

        ]

    # ------------------------------------------------------------------

    def find_by_section(
        self,
        section: str
    ) -> List[BHAComponent]:

        return [

            bha

            for bha in self.bhas

            if bha.section.lower() == section.lower()

        ]

    # ------------------------------------------------------------------

    def statistics(self) -> Dict:

        if not self.bhas:

            return {}

        total_components = sum(

            len(bha.components)

            for bha in self.bhas

        )

        avg_components = (

            total_components
            / len(self.bhas)

        )

        return {

            "bhas": len(self.bhas),

            "components": total_components,

            "average_components": avg_components,

            "max_hole_size": max(

                bha.hole_size_in

                for bha in self.bhas

            ),

            "min_hole_size": min(

                bha.hole_size_in

                for bha in self.bhas

            )

        }

    # ------------------------------------------------------------------

    def summary(self) -> None:

        print("=" * 70)
        print("BHA LIBRARY")
        print("=" * 70)

        print(f"Templates : {len(self.bhas)}")

        print()

        for bha in self.bhas:

            print(

                f"{bha.name:35}"

                f"{bha.hole_size_in:6.2f}\"   "

                f"{bha.section}"

            )

        print("=" * 70)

    def by_type(self, component_type):

        return [

            c

            for c in self.bhas  

            if c.component_type == component_type

        ]
    
    def best_bit(
    self,
    hole_size: float
) -> BHAComponent | None:
        """
        Returns the first bit matching the requested hole size.
        """

        for bha in self.bhas:

                    for component in bha.components:

                            if (
                                component.component_type == ComponentType.BIT
                                and abs(component.outside_diameter_in - hole_size) <= 0.50
                            ):
                                return component

        return None

    def best_motor(self, hole_size):

        motors = self.by_type(ComponentType.MOTOR)

        return motors[0] if motors else None

    def best_rss(self, hole_size):

        rss = self.by_type(ComponentType.RSS)

        return rss[0] if rss else None

    def best_mwd(self):

        mwd = self.by_type(ComponentType.MWD)

        return mwd[0] if mwd else None

    def best_lwd(self):

        lwd = self.by_type(ComponentType.LWD)

        return lwd[0] if lwd else None

