from bha.analytics.hydraulics import JetImpactForce


def test_jet_impact_force():

    jif = JetImpactForce(

        flow_rate_gpm=650,

        pump_pressure_psi=3200,

        bit_diameter_in=12.25,

        nozzle_diameter_in=0.50,

        nozzle_count=3,

        mud_density_ppg=10.5,

    )

    print("\n===== JIF REPORT =====")
    print(jif.summary)

    assert jif.jet_impact_force > 0


if __name__ == "__main__":
    test_jet_impact_force()