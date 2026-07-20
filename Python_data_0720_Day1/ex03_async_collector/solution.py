"""
실습 3: asyncio 기반 비동기 수집기

Semaphore로 동시 요청 수를 제한하고,
timeout과 재시도 기능을 적용한다.
"""

import asyncio
import json
import time
from pathlib import Path


TOTAL_ITEMS = 60
MAX_CONCURRENT = 10
TIMEOUT_SECONDS = 3.0
MAX_ATTMPTS = 4

OUTPUT_DIR = Path("output")
DEAD_LETTER_FILE = OUTPUT_DIR / "dead_letter.json"

# 첫 번째 요청에서 일부러 실패시킬 ID
RETRY_ITEMS = {13, 29, 47}


async def request_once(
    item_id: int,
    attempt: int,
) -> dict:
    """데이터 요청을 한 번 실행한다."""

    async with asyncio.timeout(TIMEOUT_SECONDS):
        # 네트워크 요청 대기 시간 흉내
        await asyncio.sleep(0.1)

        # 지정된 ID는 첫 번째 요청에서만 실패
        if item_id in RETRY_ITEMS and attempt == 0:
            raise RuntimeError("임시 서버 오류")

        return {
            "id": item_id,
            "ok": True,
            "attempt": attempt + 1,
        }


async def fetch_with_retry(
    item_id: int,
    semaphore: asyncio.Semaphore,
) -> dict:
    """요청이 실패하면 지수 백오프로 재시도한다."""

    for attempt in range(MAX_ATTMPTS):
        try:
            async with semaphore:
                return await request_once(
                    item_id,
                    attempt,
                )

        except (TimeoutError, RuntimeError) as error:
            # 마지막 시도까지 실패한 경우
            if attempt == MAX_ATTMPTS - 1:
                return {
                    "id": item_id,
                    "ok": False,
                    "attempt": attempt + 1,
                    "reason": str(error),
                }

            # 1초 → 2초 → 4초 대기
            wait_seconds = 2 ** attempt

            print(
                f"ID {item_id} 요청 실패: {error} "
                f"/ {wait_seconds}초 후 재시도"
            )

            await asyncio.sleep(wait_seconds)

    return {
        "id": item_id,
        "ok": False,
        "reason": "알 수 없는 오류",
    }


def save_dead_letters(failures: list[dict]) -> None:
    """최종적으로 실패한 요청을 JSON 파일로 저장한다."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with DEAD_LETTER_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            failures,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(f"실패 데이터 저장: {DEAD_LETTER_FILE}")


async def main() -> None:
    start = time.perf_counter()

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    tasks = [
        fetch_with_retry(item_id, semaphore)
        for item_id in range(TOTAL_ITEMS)
    ]

    # 한 작업에 오류가 발생해도 나머지는 계속 실행
    results = await asyncio.gather(
        *tasks,
        return_exceptions=True,
    )

    collected = [
        result
        for result in results
        if isinstance(result, dict)
    ]

    unexpected_errors = [
        result
        for result in results
        if isinstance(result, Exception)
    ]

    success = [
        result
        for result in collected
        if result.get("ok") is True
    ]

    failure = [
        result
        for result in collected
        if result.get("ok") is False
    ]

    retried = [
        result
        for result in success
        if result.get("attempt", 1) > 1
    ]

    # 최종 실패 데이터 저장
    save_dead_letters(failure)

    elapsed = time.perf_counter() - start

    print("\n수집 결과")
    print(f"전체 결과: {len(results)}건")
    print(f"성공: {len(success)}건")
    print(f"실패: {len(failure)}건")
    print(f"예상하지 못한 예외: {len(unexpected_errors)}건")
    print(f"재시도 후 성공: {len(retried)}건")
    print(f"최대 동시 요청: {MAX_CONCURRENT}개")
    print(f"실행 시간: {elapsed:.2f}초")

    if unexpected_errors:
        print("\n예외 상세")

        for error in unexpected_errors:
            print(f"- {type(error).__name__}: {error}")

    assert len(results) == TOTAL_ITEMS
    assert len(success) + len(failure) + len(unexpected_errors) == TOTAL_ITEMS
    assert len(success) == 60
    assert len(retried) == 3
    

    print("\n✅ 모든 요청이 빠짐없이 처리되었습니다.")


if __name__ == "__main__":
    asyncio.run(main())