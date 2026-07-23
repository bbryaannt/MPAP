from models import (
    LayerStatistics,
    Statistics,
)


def make_stats(mean):

    return Statistics(
        mean=mean,
        median=mean,
        standard_deviation=0.5,
        minimum=mean - 1,
        maximum=mean + 1,
    )


def main():

    layer_stats = LayerStatistics(

        area_px=make_stats(140),
        area_mm2=make_stats(0.088),

        circularity=make_stats(0.81),
        aspect_ratio=make_stats(1.05),

        mean_intensity=make_stats(39200),
        max_intensity=make_stats(54800),
        threshold=make_stats(46500),

        good_percentage=92.5,
        low_power_percentage=3.0,
        low_powder_percentage=2.0,
        high_power_percentage=1.0,
        laser_off_percentage=1.5,

        frame_count=220,
        measured_frame_count=205,
    )

    print(layer_stats)

    print()

    print(
        "Measurement %:",
        layer_stats.measurement_percentage
    )


if __name__ == "__main__":
    main()