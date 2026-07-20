import json
import sys
from pathlib import Path
from collections import Counter, defaultdict


DATA_FILE = Path("Python_Practice1_Data.json")


def high_amount_generator(sales):
    """amount가 1000보다 큰 거래를 하나씩 반환"""
    for sale in sales:
        if sale["amount"] > 1000:
            yield sale


try:
    with DATA_FILE.open(encoding="utf-8") as file:
        sales = json.load(file)

    print("데이터 불러오기 성공!")
    print("전체 거래 수:", len(sales))


    # =====================================
    # 실습 1-1 리스트 / 딕셔너리 컴프리헨션
    # =====================================

    filtered_sales = [
        sale for sale in sales
        if sale["amount"] >= 1000
    ]

    region_total = {
        region: sum(
            sale["amount"]
            for sale in sales
            if sale["region"] == region
        )
        for region in {sale["region"] for sale in sales}
    }

    print("\n=== 1000원 이상 거래 ===")
    print("거래 수:", len(filtered_sales))

    print("\n=== 지역별 총매출 ===")
    for region, total in sorted(region_total.items()):
        print(f"{region}: {total}")

    expected_region_total = {
        "서울": 20060,
        "부산": 10930,
        "대구": 12660,
        "인천": 14530,
        "광주": 9620,
        "대전": 11140,
        "울산": 11700,
        "세종": 10820
    }

    assert region_total == expected_region_total
    print("✅ region_total assert 통과!")


    # =====================================
    # 실습 1-2 Counter + defaultdict
    # =====================================

    region_counter = Counter(sale["region"] for sale in sales)

    print("\n=== 지역별 거래 건수 순위 ===")
    for region, count in region_counter.most_common():
        print(f"{region}: {count}")

    category_amounts = defaultdict(list)

    for sale in sales:
        category_amounts[sale["category"]].append(sale["amount"])

    print("\n=== 카테고리별 금액 목록 ===")
    for category, amounts in category_amounts.items():
        print(f"{category}: {amounts}")


    # =====================================
    # 실습 1-3 제너레이터 메모리 비교
    # =====================================

    high_amount_list = [
        sale for sale in sales
        if sale["amount"] > 1000
    ]
    high_amount_gen = high_amount_generator(sales)

    list_size = sys.getsizeof(high_amount_list)
    generator_size = sys.getsizeof(high_amount_gen)

    print("\n=== 리스트와 제너레이터 메모리 비교 ===")
    print("1000원 초과 거래 수:", len(high_amount_list))
    print("리스트 크기:", list_size, "bytes")
    print("제너레이터 크기:", generator_size, "bytes")

    assert generator_size < list_size
    print("✅ 제너레이터 메모리 비교 통과!")


    # =====================================
    # 실습 1-4 월별 카테고리 매출 집계
    # =====================================

    monthly_sales = defaultdict(lambda: defaultdict(int))

    for sale in sales:
        monthly_sales[sale["month"]][sale["category"]] += sale["amount"]

    monthly_category_total = {
        month: dict(categories)
        for month, categories in monthly_sales.items()
    }

    print("\n=== 월별 카테고리 매출 ===")
    for month in sorted(monthly_category_total):
        print(f"{month}: {monthly_category_total[month]}")


    # 금액이 높은 거래 TOP 3
    top3 = sorted(
        sales,
        key=lambda sale: sale["amount"],
        reverse=True
    )[:3]

    print("\n=== 금액이 높은 거래 TOP 3 ===")
    for rank, sale in enumerate(top3, start=1):
        print(
            rank,
            sale["region"],
            sale["category"],
            sale["amount"],
            sale["month"]
        )

    assert all(
        top3[index]["amount"] >= top3[index + 1]["amount"]
        for index in range(len(top3) - 1)
    )

    print("✅ TOP 3 내림차순 확인 완료!")


except FileNotFoundError:
    print(f"JSON 파일을 찾을 수 없습니다: {DATA_FILE}")

except json.JSONDecodeError:
    print("JSON 파일 형식이 올바르지 않습니다.")

except KeyError as error:
    print("필요한 데이터 항목이 없습니다:", error)

except AssertionError:
    print("검증 결과가 예상값과 다릅니다.")