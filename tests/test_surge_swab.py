from bha.analytics.hydraulics import SurgeSwabAnalysis


def test_surge_swab():

    surge = SurgeSwabAnalysis(

        mud_density_ppg=10.5,

        plastic_viscosity_cp=35,

        yield_point_lb100ft2=18,

        trip_speed_ft_min=90,

        pipe_od_in=5,

        hole_id_in=8.5,

        tvd_ft=10500,

        pipe_direction="IN",

    )

    print("\n===== SURGE / SWAB REPORT =====")

    print(surge.summary)


if __name__ == "__main__":

    test_surge_swab()