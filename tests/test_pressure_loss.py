from bha.analytics.hydraulics import PressureLossCalculator


def test_pressure_loss():

    calc = PressureLossCalculator(

        flow_rate_gpm=650,

        pump_pressure_psi=3200,

        bit_diameter_in=12.25,

        drillpipe_length_ft=10000,

        drillpipe_id_in=4.276,

        collar_length_ft=800,

        collar_id_in=2.75,

        annulus_hydraulic_diameter_in=3.50,

        mud_density_ppg=10.5,

        plastic_viscosity_cp=35,

        yield_point_lb100ft2=18,

        nozzle_pressure_loss_psi=1800,

    )

    print("\n===== PRESSURE LOSS REPORT =====")
    print(calc.summary)

    assert calc.total_pressure_loss > 0


if __name__ == "__main__":
    test_pressure_loss()