import csv
import gc
import tracemalloc
from collections import Counter
from functools import reduce


def read_logs(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            yield row


gen = read_logs("data/web_logs.csv")

for _ in range(3):
    print(next(gen))

total = 0

by_status = Counter()
by_path = Counter()
by_hour = Counter()
by_ip = Counter()

for row in read_logs("data/web_logs.csv"):
    total += 1

    # 상태코드
    by_status[row["status"]] += 1

    # 경로
    by_path[row["path"]] += 1

    # IP
    by_ip[row["ip"]] += 1

    # 시간(HH)
    hour = row["timestamp"][11:13]
    by_hour[hour] += 1

# 5xx 오류 개수 계산
err_5xx = sum(count for status, count in by_status.items() if status.startswith("5"))

# 5xx 오류율 계산
ratio = err_5xx / total * 100 if total else 0

print("=" * 40)

print(f"총 건수 : {total:,}")
print(f"5xx 오류 : {err_5xx:,}건")
print(f"5xx 오류율 : {ratio:.2f}%")

print("\n상태코드 TOP5")
print(by_status.most_common(5))

print("\n경로 TOP5")
print(by_path.most_common(5))

print("\n시간대별")
print(by_hour.most_common())

print("\n접속 IP TOP5")
print(by_ip.most_common(5))

def fold(acc, row):
    acc["total"] += 1
    acc["status"][row["status"]] += 1
    return acc


init = {
    "total": 0,
    "status": Counter()
}

reduce_result = reduce(
    fold,
    read_logs("data/web_logs.csv"),
    init
)

print("\nreduce 집계 결과")
print(f"총 건수 : {reduce_result['total']:,}")
print(f"상태코드 TOP5 : {reduce_result['status'].most_common(5)}")

import gc
import tracemalloc


def count_with_readlines(path):
    """파일 전체를 리스트로 읽어서 행 수를 센다."""

    with open(path, newline="", encoding="utf-8") as f:
        lines = f.readlines()

    reader = csv.DictReader(lines)

    return sum(1 for _ in reader)


def count_with_generator(path):
    """제너레이터로 한 행씩 읽어서 행 수를 센다."""

    return sum(1 for _ in read_logs(path))


def measure_memory(name, function, path):
    """함수를 실행하면서 최대 메모리 사용량을 측정한다."""

    gc.collect()
    tracemalloc.start()

    count = function(path)

    current, peak = tracemalloc.get_traced_memory()

    tracemalloc.stop()

    current_mb = current / 1024 / 1024
    peak_mb = peak / 1024 / 1024

    print(f"\n{name}")
    print(f"처리 건수: {count:,}건")
    print(f"현재 메모리: {current_mb:.2f} MB")
    print(f"최대 메모리: {peak_mb:.2f} MB")

    return count, peak_mb


print("\n" + "=" * 40)
print("tracemalloc 메모리 비교")

readlines_count, readlines_peak = measure_memory(
    "readlines 방식",
    count_with_readlines,
    "data/web_logs.csv",
)

generator_count, generator_peak = measure_memory(
    "제너레이터 방식",
    count_with_generator,
    "data/web_logs.csv",
)

assert readlines_count == 200_000
assert generator_count == 200_000
assert readlines_count == generator_count

print("\n메모리 비교 결과")
print(f"readlines 최대 메모리: {readlines_peak:.2f} MB")
print(f"제너레이터 최대 메모리: {generator_peak:.2f} MB")

if generator_peak > 0:
    memory_ratio = readlines_peak / generator_peak
    print(f"readlines가 약 {memory_ratio:.1f}배 더 많은 메모리를 사용했습니다.")

print("\n✅ 실습 1 확장 과제 완료")