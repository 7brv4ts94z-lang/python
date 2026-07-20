import asyncio
from pathlib import Path

import pandas as pd
from pydantic import ValidationError

from models import Product


def transform(raw: list[dict]) -> tuple[list, list]:
    valid = []
    invalid = []

    for row in raw:
        try:
            valid.append(Product(**row))

        except ValidationError as error:
            invalid.append(
                {
                    "data": row,
                    "errors": error.errors(),
                }
            )

    return valid, invalid


async def fetch(item_id: int) -> dict:
    """상품 데이터 한 건을 모의로 수집한다."""

    await asyncio.sleep(0.1)

    return {
        "id": item_id + 1,
        "name": f"Product {item_id + 1}",
        "category": " FOOD ",
        "price": float((item_id + 1) * 100),
    }


async def extract(
    ids: list[int],
    max_concurrent: int = 10,
) -> list[dict]:
    """동시 요청 수를 제한하여 상품 데이터를 수집한다."""

    sem = asyncio.Semaphore(max_concurrent)

    async def one(item_id: int):
        async with sem:
            for attempt in range(3):
                try:
                    return await fetch(item_id)

                except Exception:
                    if attempt == 2:
                        raise

                    await asyncio.sleep(2**attempt)

    results = await asyncio.gather(
        *[one(item_id) for item_id in ids],
        return_exceptions=True,
    )

    return [result for result in results if not isinstance(result, Exception)]


def load(
    valid: list,
    out_dir: str = "output",
) -> pd.DataFrame:
    """유효 데이터를 CSV와 Parquet 파일로 저장한다."""

    Path(out_dir).mkdir(
        parents=True,
        exist_ok=True,
    )

    df = pd.DataFrame([product.model_dump() for product in valid])

    df.to_csv(
        f"{out_dir}/products.csv",
        index=False,
    )

    df.to_parquet(
        f"{out_dir}/products.parquet",
        index=False,
    )

    return df


async def run(ids: list[int]) -> dict:
    """Extract, Transform, Load 단계를 순서대로 실행한다."""

    raw = await extract(ids)
    valid, invalid = transform(raw)
    df = load(valid)

    return {
        "total": len(raw),
        "valid": len(valid),
        "invalid": len(invalid),
        "rows_saved": len(df),
    }


if __name__ == "__main__":
    summary = asyncio.run(run(list(range(60))))

    print(summary)
