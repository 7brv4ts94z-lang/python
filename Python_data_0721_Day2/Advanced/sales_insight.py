"""
Advanced Project
Day2 매출 분석 및 이상 주문 탐지

사용 데이터: sales_raw.csv
주요 내용:
1. 데이터 정제
2. 지역·카테고리별 매출 분석
3. 할인 효과 분석
4. 이상 주문 탐지
5. HTML 리포트 생성
"""

import pandas as pd
import plotly.express as px

from pathlib import Path


# 현재 파일 위치를 기준으로 경로 설정
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "sales_raw.csv"

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


print("=== Day2 추가과제: 매출 데이터 분석 ===")
print(f"데이터 경로: {DATA_PATH}")


# CSV 불러오기
df = pd.read_csv(DATA_PATH)


# 데이터 기본 확인
print("\n=== 데이터 크기 ===")
print(df.shape)

print("\n=== 컬럼 이름 ===")
print(df.columns.tolist())

print("\n=== 앞 5행 ===")
print(df.head())

print("\n=== 데이터 타입 ===")
print(df.dtypes)

print("\n=== 컬럼별 결측치 개수 ===")
print(df.isna().sum())

# =========================
# 2단계: 데이터 정제
# =========================

print("\n=== 데이터 정제 시작 ===")

clean_df = df.copy()

# 날짜 형식으로 변환
clean_df["order_date"] = pd.to_datetime(
    clean_df["order_date"],
    errors="coerce",
)

# 지역 결측치는 Unknown으로 처리
clean_df["region"] = (
    clean_df["region"]
    .fillna("Unknown")
    .astype(str)
    .str.strip()
)

# 숫자형 컬럼 안전하게 변환
numeric_cols = [
    "quantity",
    "unit_price",
    "discount",
]

for col in numeric_cols:
    clean_df[col] = pd.to_numeric(
        clean_df[col],
        errors="coerce",
    )

# 음수 또는 0원인 가격은 결측치로 바꾸기
clean_df.loc[
    clean_df["unit_price"] <= 0,
    "unit_price",
] = pd.NA
# 상품 카테고리별 가격 중앙값으로 결측치 채우기
category_median_price = clean_df.groupby(
    "category"
)["unit_price"].transform("median")

clean_df["unit_price"] = (
    clean_df["unit_price"]
    .fillna(category_median_price)
    .fillna(clean_df["unit_price"].median())
)

# 수량이 없거나 0 이하인 행 제거
clean_df = clean_df[
    clean_df["quantity"].notna()
    & (clean_df["quantity"] > 0)
].copy()

# 할인율 결측치는 0으로 처리하고 0~1 범위로 제한
clean_df["discount"] = (
    clean_df["discount"]
    .fillna(0)
    .clip(0, 1)
)

# 할인 전 매출
clean_df["gross_sales"] = (
    clean_df["quantity"]
    * clean_df["unit_price"]
)

# 할인 적용 후 실제 매출
clean_df["net_sales"] = (
    clean_df["gross_sales"]
    * (1 - clean_df["discount"])
)

print(f"정제 전 데이터: {len(df):,}건")
print(f"정제 후 데이터: {len(clean_df):,}건")

print("\n=== 정제 후 결측치 ===")
print(clean_df.isna().sum())

print("\n=== 매출 계산 결과 ===")
print(
    clean_df[
        [
            "order_id",
            "quantity",
            "unit_price",
            "discount",
            "gross_sales",
            "net_sales",
        ]
    ].head()
)

print(
    f"\n전체 할인 전 매출: "
    f"{clean_df['gross_sales'].sum():,.0f}원"
)

print(
    f"전체 할인 후 매출: "
    f"{clean_df['net_sales'].sum():,.0f}원"
)

# =========================
# 3단계: 매출 집계
# =========================

print("\n=== 지역별 매출 분석 ===")

region_sales = (
    clean_df.groupby("region", as_index=False)
    .agg(
        주문수=("order_id", "count"),
        판매수량=("quantity", "sum"),
        할인전매출=("gross_sales", "sum"),
        최종매출=("net_sales", "sum"),
    )
    .sort_values("최종매출", ascending=False)
)

region_sales["할인금액"] = (
    region_sales["할인전매출"]
    - region_sales["최종매출"]
)

print(region_sales.to_string(index=False))


print("\n=== 카테고리별 매출 분석 ===")

category_sales = (
    clean_df.groupby("category", as_index=False)
    .agg(
        주문수=("order_id", "count"),
        판매수량=("quantity", "sum"),
        평균가격=("unit_price", "mean"),
        할인전매출=("gross_sales", "sum"),
        최종매출=("net_sales", "sum"),
    )
    .sort_values("최종매출", ascending=False)
)

category_sales["할인금액"] = (
    category_sales["할인전매출"]
    - category_sales["최종매출"]
)

print(category_sales.to_string(index=False))


# 집계 결과 CSV 저장
region_output_path = OUTPUT_DIR / "region_sales_summary.csv"
category_output_path = OUTPUT_DIR / "category_sales_summary.csv"

region_sales.to_csv(
    region_output_path,
    index=False,
    encoding="utf-8-sig",
)

category_sales.to_csv(
    category_output_path,
    index=False,
    encoding="utf-8-sig",
)

print("\n=== 집계 파일 저장 완료 ===")
print(region_output_path)
print(category_output_path)

# =========================
# 4단계: Plotly 시각화
# =========================

print("\n=== Plotly 그래프 생성 시작 ===")


# 1. 지역별 최종 매출 그래프
fig_region = px.bar(
    region_sales,
    x="region",
    y="최종매출",
    title="지역별 최종 매출",
    text_auto=".3s",
    hover_data=[
        "주문수",
        "판매수량",
        "할인금액",
    ],
)

fig_region.update_layout(
    xaxis_title="지역",
    yaxis_title="최종 매출",
)

region_chart_path = OUTPUT_DIR / "regional_sales.html"
fig_region.write_html(region_chart_path)


# 2. 카테고리별 최종 매출 그래프
fig_category = px.bar(
    category_sales,
    x="category",
    y="최종매출",
    title="카테고리별 최종 매출",
    text_auto=".3s",
    hover_data=[
        "주문수",
        "판매수량",
        "평균가격",
        "할인금액",
    ],
)

fig_category.update_layout(
    xaxis_title="상품 카테고리",
    yaxis_title="최종 매출",
)

category_chart_path = OUTPUT_DIR / "category_sales.html"
fig_category.write_html(category_chart_path)


# 3. 할인율과 최종 매출 관계
fig_discount = px.scatter(
    clean_df,
    x="discount",
    y="net_sales",
    color="category",
    size="quantity",
    title="할인율과 주문별 최종 매출 관계",
    hover_data=[
        "order_id",
        "region",
        "unit_price",
        "quantity",
    ],
)

fig_discount.update_layout(
    xaxis_title="할인율",
    yaxis_title="주문별 최종 매출",
)

discount_chart_path = OUTPUT_DIR / "discount_analysis.html"
fig_discount.write_html(discount_chart_path)


print("그래프 저장 완료:")
print(region_chart_path)
print(category_chart_path)
print(discount_chart_path)

# =========================
# 5단계: 이상 주문 탐지
# =========================

print("\n=== 이상 주문 탐지 시작 ===")


# IQR 방식으로 이상치 상한값 계산
def calculate_upper_limit(series):
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1

    return q3 + (1.5 * iqr)


quantity_limit = calculate_upper_limit(
    clean_df["quantity"]
)

price_limit = calculate_upper_limit(
    clean_df["unit_price"]
)

sales_limit = calculate_upper_limit(
    clean_df["net_sales"]
)


print(f"수량 이상 기준: {quantity_limit:,.2f}개 초과")
print(f"단가 이상 기준: {price_limit:,.2f}원 초과")
print(f"매출 이상 기준: {sales_limit:,.2f}원 초과")


# 이상치 여부를 새로운 컬럼으로 표시
clean_df["quantity_outlier"] = (
    clean_df["quantity"] > quantity_limit
)

clean_df["price_outlier"] = (
    clean_df["unit_price"] > price_limit
)

clean_df["sales_outlier"] = (
    clean_df["net_sales"] > sales_limit
)


# 하나라도 이상치에 해당하면 이상 주문으로 분류
abnormal_orders = clean_df[
    clean_df["quantity_outlier"]
    | clean_df["price_outlier"]
    | clean_df["sales_outlier"]
].copy()


# 이상 사유 작성
def make_abnormal_reason(row):
    reasons = []

    if row["quantity_outlier"]:
        reasons.append("판매수량 이상")

    if row["price_outlier"]:
        reasons.append("단가 이상")

    if row["sales_outlier"]:
        reasons.append("주문매출 이상")

    return ", ".join(reasons)


abnormal_orders["이상사유"] = abnormal_orders.apply(
    make_abnormal_reason,
    axis=1,
)


# 필요한 컬럼만 정리
abnormal_orders = abnormal_orders[
    [
        "order_id",
        "order_date",
        "region",
        "category",
        "quantity",
        "unit_price",
        "discount",
        "gross_sales",
        "net_sales",
        "이상사유",
    ]
].sort_values(
    "net_sales",
    ascending=False,
)


# CSV 저장
abnormal_output_path = (
    OUTPUT_DIR / "abnormal_orders.csv"
)

abnormal_orders.to_csv(
    abnormal_output_path,
    index=False,
    encoding="utf-8-sig",
)


print(f"\n이상 주문 수: {len(abnormal_orders):,}건")

print("\n=== 이상 주문 상위 10건 ===")
print(abnormal_orders.head(10).to_string(index=False))

print("\n이상 주문 파일 저장 완료:")
print(abnormal_output_path)

# =========================
# 6단계: 최종 HTML 보고서 생성
# =========================

print("\n=== 최종 분석 보고서 생성 시작 ===")

total_orders = len(clean_df)
total_quantity = clean_df["quantity"].sum()
total_gross_sales = clean_df["gross_sales"].sum()
total_net_sales = clean_df["net_sales"].sum()
total_discount = total_gross_sales - total_net_sales

top_region = region_sales.iloc[0]["region"]
top_category = category_sales.iloc[0]["category"]

region_table = region_sales.round(2).to_html(
    index=False,
    classes="data-table",
)

category_table = category_sales.round(2).to_html(
    index=False,
    classes="data-table",
)

report_html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>Day2 매출 데이터 분석 보고서</title>

    <style>
        body {{
            margin: 0;
            padding: 30px;
            background-color: #f4f6f8;
            font-family: Arial, sans-serif;
            color: #222;
        }}

        .container {{
            max-width: 1100px;
            margin: 0 auto;
        }}

        h1 {{
            text-align: center;
            margin-bottom: 10px;
        }}

        .description {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }}

        .cards {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }}

        .card {{
            background-color: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08);
        }}

        .card-title {{
            color: #666;
            font-size: 14px;
        }}

        .card-value {{
            margin-top: 10px;
            font-size: 22px;
            font-weight: bold;
        }}

        .section {{
            background-color: white;
            padding: 25px;
            margin-bottom: 25px;
            border-radius: 12px;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08);
        }}

        .data-table {{
            width: 100%;
            border-collapse: collapse;
        }}

        .data-table th,
        .data-table td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
            text-align: center;
        }}

        .data-table th {{
            background-color: #eef2f5;
        }}

        .chart-links a {{
            display: inline-block;
            margin: 5px 10px 5px 0;
            padding: 10px 15px;
            background-color: #333;
            color: white;
            text-decoration: none;
            border-radius: 7px;
        }}

        .chart-links a:hover {{
            background-color: #555;
        }}

        .warning {{
            padding: 15px;
            border-left: 5px solid orange;
            background-color: #fff7e6;
        }}

        @media screen and (max-width: 700px) {{
            .cards {{
                grid-template-columns: 1fr;
            }}

            body {{
                padding: 15px;
            }}
        }}
    </style>
</head>

<body>
<div class="container">

    <h1>Day2 매출 데이터 분석 보고서</h1>

    <p class="description">
        sales_raw.csv 데이터 정제·매출 집계·시각화·이상 주문 분석
    </p>

    <div class="cards">
        <div class="card">
            <div class="card-title">전체 주문 수</div>
            <div class="card-value">{total_orders:,}건</div>
        </div>

        <div class="card">
            <div class="card-title">전체 판매 수량</div>
            <div class="card-value">{total_quantity:,.0f}개</div>
        </div>

        <div class="card">
            <div class="card-title">할인 후 최종 매출</div>
            <div class="card-value">{total_net_sales:,.0f}원</div>
        </div>

        <div class="card">
            <div class="card-title">할인 전 매출</div>
            <div class="card-value">{total_gross_sales:,.0f}원</div>
        </div>

        <div class="card">
            <div class="card-title">전체 할인 금액</div>
            <div class="card-value">{total_discount:,.0f}원</div>
        </div>

        <div class="card">
            <div class="card-title">탐지된 이상 주문</div>
            <div class="card-value">{len(abnormal_orders):,}건</div>
        </div>
    </div>

    <div class="section">
        <h2>핵심 분석 결과</h2>

        <p>
            최종 매출이 가장 높은 지역은
            <strong>{top_region}</strong>입니다.
        </p>

        <p>
            최종 매출이 가장 높은 상품 카테고리는
            <strong>{top_category}</strong>입니다.
        </p>

        <div class="warning">
            수량·단가·주문 매출의 IQR 기준을 이용해
            이상 주문 {len(abnormal_orders):,}건을 탐지했습니다.
        </div>
    </div>

    <div class="section">
        <h2>지역별 매출 집계</h2>
        {region_table}
    </div>

    <div class="section">
        <h2>카테고리별 매출 집계</h2>
        {category_table}
    </div>

    <div class="section chart-links">
        <h2>상세 그래프</h2>

        <a href="regional_sales.html">
            지역별 매출 그래프
        </a>

        <a href="category_sales.html">
            카테고리별 매출 그래프
        </a>

        <a href="discount_analysis.html">
            할인율 분석 그래프
        </a>
    </div>

</div>
</body>
</html>
"""

report_path = OUTPUT_DIR / "sales_report.html"

report_path.write_text(
    report_html,
    encoding="utf-8",
)

print("최종 HTML 보고서 생성 완료:")
print(report_path)