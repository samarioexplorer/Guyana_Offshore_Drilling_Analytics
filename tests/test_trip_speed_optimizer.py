from bha.analytics.optimization import TripSpeedOptimizer


def test_trip_speed_optimizer():

    optimizer = TripSpeedOptimizer(

        trip_speed_ft_min=90,

        kick_margin_ppg=0.21,

        fracture_margin_ppg=1.87,

        window_utilization=35.2,

        hydraulic_score=90,

    )

    print("\n===== TRIP SPEED OPTIMIZER =====")

    print(optimizer.summary)


if __name__ == "__main__":

    test_trip_speed_optimizer()