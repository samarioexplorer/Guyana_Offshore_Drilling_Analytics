from bha.analytics.hydraulics import PressureWindowAnalyzer


def test_pressure_window():

    analyzer = PressureWindowAnalyzer(

        pore_pressure_ppg=10.20,

        fracture_gradient_ppg=12.50,

        mud_weight_ppg=10.50,

        ecd_ppg=11.01,

        surge_density_ppg=10.63,

        swab_density_ppg=10.41,

    )

    print()
    print("===== PRESSURE WINDOW REPORT =====")
    print(analyzer.summary)


if __name__ == "__main__":
    test_pressure_window()