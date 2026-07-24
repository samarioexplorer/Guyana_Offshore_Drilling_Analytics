from bha.assembly import BottomHoleAssembly
from bha.engineering import (
    BHAEngineering,
)

from bha.engineering.survey import (
    SurveyStation,
)

bha = BottomHoleAssembly(
    name="Survey Test",
    section="Build",
    hole_size_in=12.25,
)

eng = BHAEngineering(bha)

stations = [

    SurveyStation(0,0,0),

    SurveyStation(100,5,15),

    SurveyStation(200,12,22),

    SurveyStation(300,20,30),

    SurveyStation(400,28,37),

    SurveyStation(500,35,45),

]

stations = eng.process_survey(stations)

print()

print(" MD      TVD      North      East      Closure      Azi      DLS")

print("-"*70)

for s in stations:

    print(

        f"{s.md:5.0f}"

        f"{s.tvd:10.2f}"

        f"{s.northing:11.2f}"

        f"{s.easting:10.2f}"

        f"{s.closure:12.2f}"

        f"{s.closure_azimuth:10.2f}"

        f"{s.dls:10.2f}"

    )