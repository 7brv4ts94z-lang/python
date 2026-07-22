from pathlib import Path

import pandas as pd


# Pandas 2.x Copy-on-Write 활성화
pd.options.mode.copy_on_write = True


# 데이터 파일 경로
DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "sales_raw.csv"
)


# =========================================================
# 확장 과제: 데이터 정제 함수를 단계별로 분리
# =========================================================

def diagnose(dataframe):
    """데이터의 크기, 타입, 결측값, 수치형 요약을 확인한다."""

    print("=== STEP 0: 데이터 진단 ===")

    print("\n1. 데이터 크기")
    print(dataframe.shape)

    print("\n2. 컬럼 정보")
    dataframe.info()

    print("\n3. 수치형 데이터 요약")
    print(dataframe.describe())

    print("\n4. 컬럼별 결측값")
    print(dataframe.isna().sum())

    print("\n5. 처음 5개 데이터")
    print(dataframe.head())


def normalize_types(dataframe):
    """각 컬럼을 분석에 적합한 데이터 타입으로 변환한다."""

    cleaned = dataframe.copy()

    # 숫자로 변환할 수 없는 값은 NaN으로 처리
    cleaned["unit_price"] = pd.to_numeric(
        cleaned["unit_price"],
        errors="coerce",
    )

    cleaned["quantity"] = pd.to_numeric(
        cleaned["quantity"],
        errors="coerce",
    )

    cleaned["discount"] = pd.to_numeric(
        cleaned["discount"],
        errors="coerce",
    )

    # 날짜 타입으로 변환
    cleaned["order_date"] = pd.to_datetime(
        cleaned["order_date"],
        errors="coerce",
    )

    # 범주형 타입으로 변환
    cleaned["category"] = cleaned["category"].astype("category")

    return cleaned


def fill_missing(dataframe):
    """unit_price 결측값을 카테고리별 중앙값으로 채운다."""

    cleaned = dataframe.copy()

    # 각 행이 속한 카테고리의 중앙값 계산
    category_median = (
        cleaned.groupby(
            "category",
            observed=True,
        )["unit_price"]
        .transform("median")
    )

    # 카테고리별 중앙값으로 결측값 대체
    cleaned["unit_price"] = cleaned["unit_price"].fillna(
        category_median
    )

    # 카테고리 전체가 결측인 경우를 대비한 최종 처리
    cleaned["unit_price"] = cleaned["unit_price"].fillna(
        cleaned["unit_price"].median()
    )

    return cleaned


def winsorize_series(series, k=1.5):
    """IQR 범위를 벗어나는 값을 경계값으로 조정한다."""

    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)

    iqr = q3 - q1

    lower_limit = q1 - k * iqr
    upper_limit = q3 + k * iqr

    cleaned_series = series.clip(
        lower=lower_limit,
        upper=upper_limit,
    )

    return cleaned_series, lower_limit, upper_limit


def remove_outliers(dataframe):
    """unit_price 이상치를 IQR 윈저라이징 방식으로 처리한다."""

    cleaned = dataframe.copy()

    before_min = cleaned["unit_price"].min()
    before_max = cleaned["unit_price"].max()

    (
        cleaned["unit_price"],
        lower_limit,
        upper_limit,
    ) = winsorize_series(cleaned["unit_price"])

    after_min = cleaned["unit_price"].min()
    after_max = cleaned["unit_price"].max()

    result = {
        "before_min": before_min,
        "before_max": before_max,
        "lower_limit": lower_limit,
        "upper_limit": upper_limit,
        "after_min": after_min,
        "after_max": after_max,
    }

    return cleaned, result


def create_amount(dataframe):
    """수량, 단가, 할인율을 이용해 실제 매출액을 계산한다."""

    cleaned = dataframe.copy()

    cleaned["amount"] = (
        cleaned["unit_price"]
        * cleaned["quantity"]
        * (1 - cleaned["discount"])
    )

    return cleaned


def create_summary(dataframe):
    """카테고리별 주문 수, 단가, 판매량, 매출을 집계한다."""

    summary = (
        dataframe.groupby(
            "category",
            observed=True,
        )
        .agg(
            주문건수=("order_id", "count"),
            평균단가=("unit_price", "mean"),
            중앙단가=("unit_price", "median"),
            총판매수량=("quantity", "sum"),
            총매출=("amount", "sum"),
        )
        .round(1)
    )

    return summary


def create_pivot(dataframe):
    """카테고리별·지역별 총매출 교차표를 만든다."""

    pivot = dataframe.pivot_table(
        index="category",
        columns="region",
        values="amount",
        aggfunc="sum",
        fill_value=0,
        observed=True,
    ).round(1)

    return pivot


def merge_category_info(dataframe):
    """카테고리 코드가 들어 있는 별도 표를 만들어 결합한다."""

    category_info = (
        dataframe[["category"]]
        .drop_duplicates()
        .sort_values("category")
        .reset_index(drop=True)
    )

    category_info["category_code"] = [
        f"C{number:02d}"
        for number in range(
            1,
            len(category_info) + 1,
        )
    ]

    merged = dataframe.merge(
        category_info,
        on="category",
        how="left",
        validate="many_to_one",
    )

    return merged, category_info


def add_high_price_flag(dataframe, threshold=100_000):
    """기준 가격을 넘는 주문에 고가 상품 표시를 추가한다."""

    cleaned = dataframe.copy()

    cleaned["high_price_flag"] = 0

    # 체인 인덱싱 대신 loc 사용
    cleaned.loc[
        cleaned["unit_price"] > threshold,
        "high_price_flag",
    ] = 1

    return cleaned


def run_checks(raw_dataframe, cleaned_dataframe, merged_dataframe):
    """정제 함수가 올바르게 작동했는지 자동으로 확인한다."""

    # 정제 전후 행 개수가 같은지 확인
    assert len(raw_dataframe) == len(cleaned_dataframe)

    # unit_price 결측값이 모두 처리됐는지 확인
    assert cleaned_dataframe["unit_price"].isna().sum() == 0

    # 날짜 타입으로 변환됐는지 확인
    assert pd.api.types.is_datetime64_any_dtype(
        cleaned_dataframe["order_date"]
    )

    # category 타입으로 변환됐는지 확인
    assert str(cleaned_dataframe["category"].dtype) == "category"

    # amount 컬럼이 생성됐는지 확인
    assert "amount" in cleaned_dataframe.columns

    # merge 전후 행 개수가 같은지 확인
    assert len(cleaned_dataframe) == len(merged_dataframe)

    # 결합한 카테고리 코드에 결측값이 없는지 확인
    assert merged_dataframe["category_code"].isna().sum() == 0

    print("\n모든 자동 검증을 통과했습니다.")


# =========================================================
# 프로그램 실행
# =========================================================

# CSV 데이터 불러오기
raw_df = pd.read_csv(DATA_PATH)


# STEP 0: 데이터 진단
diagnose(raw_df)


# STEP 1: 타입 정규화
print("\n=== STEP 1: 타입 정규화 ===")

df = normalize_types(raw_df)

print("\n변환 후 데이터 타입:")
print(df.dtypes)

print("\n변환 후 결측값:")
print(df.isna().sum())


# STEP 2: 결측값 처리
print("\n=== STEP 2: 결측값 처리 ===")

before_missing = df["unit_price"].isna().sum()

df = fill_missing(df)

after_missing = df["unit_price"].isna().sum()

print("처리 전 결측값:", before_missing)
print("처리 후 결측값:", after_missing)


# STEP 3: 이상치 처리
print("\n=== STEP 3: 이상치 처리 ===")

df, outlier_result = remove_outliers(df)

print("처리 전 최솟값:", outlier_result["before_min"])
print("처리 전 최댓값:", outlier_result["before_max"])
print("IQR 하한값:", outlier_result["lower_limit"])
print("IQR 상한값:", outlier_result["upper_limit"])
print("처리 후 최솟값:", outlier_result["after_min"])
print("처리 후 최댓값:", outlier_result["after_max"])


# 주문별 실제 매출액 생성
df = create_amount(df)


# STEP 4: groupby.agg 집계
print("\n=== STEP 4: 카테고리별 요약 ===")

summary = create_summary(df)

print(summary)


# STEP 5: pivot_table 집계
print("\n=== STEP 5: 카테고리별·지역별 매출 교차표 ===")

pivot = create_pivot(df)

print(pivot)


# STEP 6: merge
print("\n=== STEP 6: 카테고리 정보 표 결합 ===")

merged, category_info = merge_category_info(df)

print("\n카테고리 정보 표:")
print(category_info)

print("\nmerge 전후 행 개수:")
print(len(df), "→", len(merged))

print("\n결합 결과:")
print(
    merged[
        [
            "order_id",
            "category",
            "category_code",
        ]
    ].head()
)


# STEP 7: Copy-on-Write와 loc
print("\n=== STEP 7: Copy-on-Write와 loc ===")

df = add_high_price_flag(
    df,
    threshold=100_000,
)

print("\n고가 상품 표시 결과:")
print(
    df[
        [
            "order_id",
            "unit_price",
            "high_price_flag",
        ]
    ].head(10)
)

print("\n고가 상품 개수:")
print(df["high_price_flag"].value_counts())


# 확장 과제 자동 검증
print("\n=== 확장 과제 자동 검증 ===")

run_checks(
    raw_dataframe=raw_df,
    cleaned_dataframe=df,
    merged_dataframe=merged,
)


# 최종 점검
print("\n=== 실습 4 최종 점검 ===")

print("\n1. 전체 행과 열 개수")
print(df.shape)

print("\n2. 최종 데이터 타입")
print(df.dtypes)

print("\n3. 최종 결측값 개수")
print(df.isna().sum())

print("\n4. unit_price 최솟값과 최댓값")
print("최솟값:", df["unit_price"].min())
print("최댓값:", df["unit_price"].max())

print("\n5. merge 전후 행 개수")
print(len(df), "→", len(merged))

print("\n6. 최종 데이터 앞 5행")
print(df.head())