from bha.analytics.hydraulics import BottomHolePressure


def test_bhp():

    bhp = BottomHolePressure(

        mud_weight_ppg=10.5,

        tvd_ft=10500,

        annular_pressure_loss_psi=280,

        surge_pressure_psi=70,

        swab_pressure_psi=50,

        pore_pressure_ppg=10.2,

        fracture_gradient_ppg=12.5
    )

    print()
    print("===== BHP REPORT =====")
    print(bhp.summary)


if __name__ == "__main__":
    test_bhp()