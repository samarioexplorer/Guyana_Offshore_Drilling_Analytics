from bha.analytics.drilling_performance import DrillingPerformance


def test_drilling_performance():

    perf = DrillingPerformance(
        footage_ft=1200,
        drilling_hours=30,
        on_bottom_hours=24,
        rotary_hours=18,
        sliding_hours=6,
        circulating_hours=4,
        trip_hours=5,
        npt_hours=3,
        connection_hours=2,
    )

    assert round(perf.average_rop, 2) == 40.00
    assert round(perf.mechanical_rop, 2) == 50.00
    assert round(perf.rotary_percentage, 1) == 75.0
    assert round(perf.sliding_percentage, 1) == 25.0