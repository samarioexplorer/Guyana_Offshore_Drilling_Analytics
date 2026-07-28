from bha.analytics.bit_performance import BitPerformance


def test_bit_performance():

    bit = BitPerformance(
        bit_number=3,
        bit_type="PDC",
        manufacturer="Smith Bits",
        footage_ft=1850,
        drilling_hours=46.5,
        rotating_hours=42.0,
        bit_cost_usd=22500,
        iadc_dull_grade="1-1-WT-A-X-I-NO-TD",
    )

    print(bit.summary)

    assert round(bit.average_rop, 2) == 39.78
    assert round(bit.cost_per_foot, 2) == 12.16
    assert bit.recommendation == "Continue using this bit model"


if __name__ == "__main__":
    test_bit_performance()