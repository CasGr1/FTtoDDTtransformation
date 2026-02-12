from plot import load_data_in_10s
import statistics


def compute_stats_per_bucket(file, column="time(s)"):
    buckets = load_data_in_10s(file, column)

    results = []
    for i, bucket in enumerate(buckets):
        lower = i * 10
        upper = lower + 9

        if len(bucket) == 0:
            avg = median = max_val = None
        else:
            avg = sum(bucket) / len(bucket)
            median = statistics.median(bucket)
            max_val = max(bucket)

        results.append({
            "range": f"{lower}-{upper}",
            "count": len(bucket),
            "average": avg,
            "median": median,
            "max": max_val
        })

    return results


if __name__ == "__main__":
    file_path = "Results/Old/BUDATESTDAG.csv"  # <-- change this
    stats = compute_stats_per_bucket(file_path, column="time(s)")

    for bucket in stats:
        print(f"BES {bucket['range']}:")
        print(f"  Count   : {bucket['count']}")
        print(f"  Average : {bucket['average']}")
        print(f"  Median  : {bucket['median']}")
        print(f"  Max     : {bucket['max']}")
        print()