"""
실습 2: Pydantic v2 중첩 스키마 검증

주요 기능
1. api_response.json 파일을 읽는다.
2. 중첩된 profile 데이터까지 Pydantic으로 검증한다.
3. 정상 데이터와 오류 데이터를 분리한다.
4. 오류가 발생한 ID, 필드, 실패 사유를 출력한다.
"""

import json
from datetime import date
from pathlib import Path
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    field_validator,
)


DATA_FILE = Path("data/api_response.json")
OUTPUT_DIR = Path("output")
ERROR_FILE = OUTPUT_DIR / "validation_errors.json"

Age = Annotated[int, Field(ge=0, le=120)]
Score = Annotated[float, Field(ge=0, le=100)]


class Profile(BaseModel):
    """사용자의 중첩 프로필 검증 모델."""

    country: Literal["KR", "US", "JP", "DE"]
    tier: Literal["free", "pro", "enterprise"]
    score: Score


class UserRecord(BaseModel):
    """사용자 한 명의 데이터 검증 모델."""

    id: int = Field(gt=0)
    username: str
    email: str
    age: Age
    is_active: bool
    signup_date: date
    profile: Profile
    tags: list[str]

    @field_validator("email")
    @classmethod
    def check_email(cls, value: str) -> str:
        """간단한 이메일 형식을 검사한다."""

        if "@" not in value:
            raise ValueError("이메일에 @가 없습니다.")

        domain = value.split("@")[-1]

        if "." not in domain:
            raise ValueError("올바른 이메일 도메인이 아닙니다.")

        return value


def load_json(file_path: Path) -> dict:
    """JSON 파일을 읽어 딕셔너리로 반환한다."""

    try:
        with file_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {file_path}")
        return {}

    except json.JSONDecodeError as error:
        print(f"JSON 형식 오류: {error}")
        return {}


def validate_records(
    records: list[dict],
) -> tuple[list[dict], list[dict]]:
    """회원 데이터를 검증하고 정상·오류 데이터로 분리한다."""

    valid = []
    errors = []

    for row in records:
        try:
            user = UserRecord.model_validate(row)
            valid.append(user.model_dump())

        except ValidationError as error:
            errors.append({
                "id": row.get("id"),
                "errors": error.errors(include_context=False),
            })

    return valid, errors


def print_error_report(errors: list[dict]) -> None:
    """검증에 실패한 데이터의 상세 사유를 출력한다."""

    print("\n오류 상세")

    for item in errors:
        print(f"\nID: {item['id']}")

        for error in item["errors"]:
            field = ".".join(
                str(value)
                for value in error["loc"]
            )

            print(f"필드: {field}")
            print(f"사유: {error['msg']}")

def save_error_report(errors: list[dict]) -> None:
    """검증 오류를 JSON 파일로 저장한다."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with ERROR_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            errors,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(f"\n오류 리포트 저장 완료: {ERROR_FILE}")            


def main() -> None:
    data = load_json(DATA_FILE)

    if not data:
        return

    records = data.get("results", [])

    valid, errors = validate_records(records)

    print(f"상태: {data.get('status')}")
    print(f"전체 데이터: {len(records)}")
    print(f"유효 데이터: {len(valid)}")
    print(f"오류 데이터: {len(errors)}")

    print_error_report(errors)
    save_error_report(errors)

    # 체크포인트
    assert len(records) == 40
    assert len(valid) == 36
    assert len(errors) == 4

    print("\n✅ 유효 36건 / 오류 4건 검증 완료")
    print("✅ 확장 과제: 오류 리포트 JSON 저장 완료")


if __name__ == "__main__":
    main()