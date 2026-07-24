from bha.analytics.drilling_performance import DrillingPerformance
from bha.analytics.drilling_kpi import DrillingKPI


def test_drilling_kpi():

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

    kpi = DrillingKPI(perf)

    assert kpi.score > 0

    assert isinstance(kpi.rating, str)

    assert isinstance(kpi.recommendations, list)

    print(kpi.summary)


if __name__ == "__main__":
    test_drilling_kpi()