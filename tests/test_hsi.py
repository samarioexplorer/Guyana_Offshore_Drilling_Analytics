from bha.analytics.hydraulics import HydraulicHorsepowerPerSquareInch


def test_hsi():

    hsi = HydraulicHorsepowerPerSquareInch(
        flow_rate_gpm=650,
        pump_pressure_psi=3200,
        bit_diameter_in=12.25,
    )

    print("\n===== HSI REPORT =====")
    print(hsi.summary)

    assert hsi.hsi > 0


if __name__ == "__main__":
    test_hsi()