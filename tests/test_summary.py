from pprint import pprint

from bha.assembly import BottomHoleAssembly
from bha.engineering import BHAEngineering

bha = BottomHoleAssembly(
    name="Summary Demo",
    section="Build",
    hole_size_in=12.25,
)

eng = BHAEngineering(bha)

pprint(eng.summary)