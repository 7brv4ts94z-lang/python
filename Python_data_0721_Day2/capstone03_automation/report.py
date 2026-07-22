import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
from jinja2 import Environment, FileSystemLoader

from config import CONFIG
from notifier import send_notifications


def aggregate(df: pd.DataFrame, top_n: int = 10) -> dict:
    """데이터를 받아 리포트에 넣을 값을 계산합니다."""
    return {
        "kpi": {
            "총매출": int(df["amount"].sum()),
            "주문수": len(df),
            "평균주문액": round(df["amount"].mean(), 1),
        },
        "by_category": (
            df.groupby("category", observed=True)["amount"]
            .sum()
            .sort_values(ascending=False)
            .head(top_n)
            .reset_index()
            .to_dict("records")
        ),
        "daily_sales": (
    df.groupby("order_date", observed=True)["amount"]
    .sum()
    .reset_index()
),
    }
def make_chart(daily_sales: pd.DataFrame) -> str:
    """일별 매출을 Plotly 차트 HTML로 만듭니다."""

    fig = px.line(
        daily_sales,
        x="order_date",
        y="amount",
        markers=True,
        title="일별 매출 추이",
        labels={
            "order_date": "주문일",
            "amount": "매출액",
        },
    )

    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
    )

    return fig.to_html(
        full_html=False,
        include_plotlyjs="cdn",
    )
def render(data: dict, cfg=CONFIG) -> Path:
    """집계 결과를 HTML 리포트로 저장합니다."""

    env = Environment(
        loader=FileSystemLoader("templates")
    )

    template = env.get_template("report.html")

    now = datetime.now()

    html = template.render(
    title=cfg.title,
    generated_at=now.strftime("%Y-%m-%d %H:%M:%S"),
    chart_html=make_chart(data["daily_sales"]),
    **data,
)

    cfg.output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    stamp = now.strftime("%Y%m%d_%H%M%S")
    output_path = cfg.output_dir / f"report_{stamp}.html"

    output_path.write_text(
        html,
        encoding="utf-8",
    )

    return output_path


def run_with_retry(cfg=CONFIG) -> Path:
    """실제 매출 데이터로 리포트를 한 번 생성합니다."""

    df = pd.read_csv(cfg.data_path)

    df["quantity"] = pd.to_numeric(
        df["quantity"],
        errors="coerce",
    )

    df["unit_price"] = pd.to_numeric(
        df["unit_price"],
        errors="coerce",
    )

    df["discount"] = pd.to_numeric(
        df["discount"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "category",
            "quantity",
            "unit_price",
            "discount",
        ]
    )

    df = df[
        (df["quantity"] > 0)
        & (df["unit_price"] > 0)
        & (df["discount"].between(0, 1))
    ].copy()

    df["amount"] = (
        df["quantity"]
        * df["unit_price"]
        * (1 - df["discount"])
    )

    data = aggregate(
        df,
        cfg.top_n,
    )

    output_path = render(
        data,
        cfg,
    )

    send_notifications(output_path)

    print("리포트 생성 완료:", output_path)

    return output_path
def run_with_retry(
    task=None,
    max_attempts: int = 3,
    base_delay: int = 2,
):
    """실패하면 2초, 4초 간격으로 재시도합니다."""

    if task is None:
        task = run_with_retry

    for attempt in range(1, max_attempts + 1):
        try:
            return task()

        except Exception as error:
            if attempt == max_attempts:
                print(
                    f"최종 실패: {max_attempts}번 시도했습니다."
                )
                raise

            delay = base_delay * (2 ** (attempt - 1))

            print(
                f"{attempt}번째 시도 실패: {error}"
            )
            print(
                f"{delay}초 후 재시도합니다."
            )

            time.sleep(delay)


if __name__ == "__main__":
    run_with_retry()

    