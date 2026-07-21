import asyncio

import pandas as pd

from SKALA_PYTHON.Python_data_0720_Day1.capstone01_async_etl.pipeline import extract, run, transform


def test_카테고리_소문자화():
    valid, _ = transform(
        [
            {
                "id": 1,
                "name": "A",
                "category": "  FOOD  ",
                "price": 10,
            }
        ]
    )

    assert valid[0].category == "food"


def test_음수_가격_거부():
    valid, invalid = transform(
        [
            {
                "id": 1,
                "name": "A",
                "category": "food",
                "price": -5,
            }
        ]
    )

    assert len(valid) == 0
    assert len(invalid) == 1


def test_유효_무효_건수_일치():
    rows = [
        {
            "id": 1,
            "name": "A",
            "category": "food",
            "price": 10,
        },
        {
            "id": 2,
            "name": "B",
            "category": "books",
            "price": 20,
        },
        {
            "id": 3,
            "name": "C",
            "category": "food",
            "price": -5,
        },
    ]

    valid, invalid = transform(rows)

    assert len(valid) + len(invalid) == len(rows)


def test_parquet_라운드트립(tmp_path):
    df = pd.DataFrame(
        {
            "id": [1, 2],
            "price": [10.5, 20.0],
        }
    )

    parquet_file = tmp_path / "test.parquet"

    df.to_parquet(
        parquet_file,
        index=False,
    )

    back = pd.read_parquet(parquet_file)

    pd.testing.assert_frame_equal(
        df,
        back,
    )


def test_비동기_수집_60건():
    raw = asyncio.run(extract(list(range(60))))

    assert len(raw) == 60


def test_run_전체_파이프라인(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)

    summary = asyncio.run(run(list(range(3))))

    assert summary == {
        "total": 3,
        "valid": 3,
        "invalid": 0,
        "rows_saved": 3,
    }

    assert (tmp_path / "output" / "products.csv").exists()

    assert (tmp_path / "output" / "products.parquet").exists()
