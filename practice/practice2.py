"""
07/20 광주_3반_박현수
Practice 2: 파일 I/O, 예외 처리, Pydantic 검증 파이프라인

- 원본 JSON은 수정하지 않고 검증용 데이터 7건을 구성한다.
- Pydantic으로 정상 4건과 오류 3건을 분리한다.
- 정상 데이터는 CSV, 오류 데이터는 JSON으로 저장한다.
- 저장된 CSV를 다시 읽어 결과를 확인한다.
"""

import csv
import json
import logging
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, ValidationError, field_validator


INPUT_FILE = Path("Python_Practice2_Checkpoint.json")
VALID_FILE = Path("valid_sales.csv")
ERROR_FILE = Path("error_sales.json")

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


def safe_load_csv(file_path: Path) -> list[dict] | None:
    """CSV 파일을 안전하게 읽는다."""

    try:
        with file_path.open(
            "r",
            encoding="utf-8",
            newline=""
        ) as file:
            data = list(csv.DictReader(file))

        logger.info("CSV 로딩 성공")
        return data

    except FileNotFoundError:
        logger.error("CSV 파일이 존재하지 않습니다.")
        return None

    except csv.Error as error:
        logger.error("CSV 형식 오류: %s", error)
        return None

    finally:
        print("로딩 종료")


def safe_load_json(file_path: Path) -> list[dict] | None:
    """JSON 파일을 안전하게 읽는다."""

    try:
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        logger.info("JSON 로딩 성공")
        return data

    except FileNotFoundError:
        logger.error("JSON 파일이 존재하지 않습니다.")
        return None

    except json.JSONDecodeError as error:
        logger.error("JSON 형식 오류: %s", error)
        return None


class SalesRecord(BaseModel):
    """판매 데이터의 검증 규칙이다."""

    month: str
    region: str
    amount: float = Field(gt=0)
    category: Optional[str] = None

    @field_validator("month", "region")
    @classmethod
    def check_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("빈 값은 허용되지 않습니다.")
        return value


def build_test_data(source_data: list[dict]) -> list[dict]:
    """원본을 수정하지 않고 정상 4건과 오류 3건을 만든다."""

    if len(source_data) < 7:
        raise ValueError("원본 데이터가 7건 이상 필요합니다.")

    raw_data = [row.copy() for row in source_data[:4]]

    error_rules = [
        (4, "month", ""),
        (5, "region", ""),
        (6, "amount", -300)
    ]

    for index, field, value in error_rules:
        row = source_data[index].copy()
        row[field] = value
        raw_data.append(row)

    return raw_data


def validate_data(
    raw_data: list[dict]
) -> tuple[list[dict], list[dict]]:
    """Pydantic으로 정상 데이터와 오류 데이터를 분리한다."""

    valid = []
    errors = []

    for row in raw_data:
        try:
            record = SalesRecord.model_validate(row)
            valid.append(record.model_dump())

        except ValidationError as error:
            print("\n검증 오류 발생")
            print(error)

            errors.append({
                "row": row,
                "error": error.errors(include_context=False)
            })

    return valid, errors


def save_results(valid: list[dict], errors: list[dict]) -> None:
    """검증 결과를 CSV와 JSON으로 저장한다."""

    with VALID_FILE.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["month", "region", "amount", "category"]
        )
        writer.writeheader()
        writer.writerows(valid)

    with ERROR_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            errors,
            file,
            ensure_ascii=False,
            indent=4
        )

    logger.info("결과 파일 저장 완료")


def main() -> None:
    # 체크포인트 1: 없는 파일이면 None 반환
    assert safe_load_csv(Path("없는파일.csv")) is None
    print("✅ safe_load_csv 테스트 완료")

    source_data = safe_load_json(INPUT_FILE)

    if source_data is None:
        logger.error("입력 데이터를 읽지 못했습니다.")
        return

    print(f"원본 데이터 개수: {len(source_data)}")

    try:
        raw_data = build_test_data(source_data)
    except ValueError as error:
        logger.error("데이터 구성 오류: %s", error)
        return

    print(f"검증 대상 데이터 개수: {len(raw_data)}")

    valid, errors = validate_data(raw_data)

    print(f"\n정상 데이터: {len(valid)}")
    print(f"오류 데이터: {len(errors)}")

    # 체크포인트 2, 3
    assert len(valid) == 4
    assert len(errors) == 3
    print("✅ valid 4건 / errors 3건 검증 완료")

    save_results(valid, errors)

    # 체크포인트 4: 저장 결과 재로딩
    reloaded = safe_load_csv(VALID_FILE)

    assert reloaded is not None
    assert len(reloaded) == 4

    print(f"재로딩 데이터 개수: {len(reloaded)}")
    print("✅ Practice 2 완료")


if __name__ == "__main__":
    main()