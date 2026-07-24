from bha.assembly import BottomHoleAssembly
from bha.engineering import BHAEngineering
from bha.engineering.survey import SurveyStation

bha = BottomHoleAssembly(
    name="Survey Analytics",
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

eng.process_survey(stations)

print("===== SURVEY ANALYSIS =====")
print(f"Stations          : {eng.survey_station_count}")
print(f"Final TVD         : {eng.final_tvd:.2f}")
print(f"Final Northing    : {eng.final_northing:.2f}")
print(f"Final Easting     : {eng.final_easting:.2f}")
print(f"Final Closure     : {eng.final_closure:.2f}")
print(f"Maximum DLS       : {eng.max_dls:.2f}")
print(f"Average DLS       : {eng.average_dls:.2f}")
print(f"Maximum Incl.     : {eng.maximum_inclination:.2f}")
print(f"Well Type         : {eng.well_type}")
print(f"Survey Quality    : {eng.survey_quality}")