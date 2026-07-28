from bha.analytics.mse import MechanicalSpecificEnergy


def test_mse():

    mse = MechanicalSpecificEnergy(

        well_name="Liza-2",

        bit_number=3,

        bit_type="PDC",

        bit_diameter_in=12.25,

        wob_klbf=45,

        torque_ftlb=15000,

        rpm=140,

        rop_ft_hr=55,

        flow_rate_gpm=650,

        standpipe_pressure_psi=3200,

        mud_weight_ppg=11.8,

        ucs_psi=35000,

        motor_torque_ftlb=0,

    )

    print("\n===== MSE REPORT =====")
    print(mse.summary)

    # Basic engineering checks
    assert mse.bit_area > 0
    assert mse.axial_energy > 0
    assert mse.rotary_energy > 0
    assert mse.mse > 0

    # Formation comparison
    assert mse.mse_ratio is not None
    assert mse.mse_ratio > 0

    # Engineering outputs
    assert mse.efficiency in (
        "Excellent",
        "Good",
        "Fair",
        "Poor",
    )

    assert isinstance(
        mse.optimization_recommendations,
        list,
    )

    assert len(
        mse.optimization_recommendations
    ) > 0


if __name__ == "__main__":

    test_mse()