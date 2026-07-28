from bha.analytics.hydraulics import HydraulicHorsepower


def test_hydraulic_horsepower():

    hhp = HydraulicHorsepower(
        flow_rate_gpm=650,
        pump_pressure_psi=3200,
        bit_diameter_in=12.25,
    )

    print("\n===== HHP REPORT =====")
    print(hhp.summary)

    assert round(hhp.hhp, 1) == 1213.5


if __name__ == "__main__":
    test_hydraulic_horsepower()