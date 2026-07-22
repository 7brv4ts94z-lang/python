import argparse
import time

import schedule

from report import run_once


def run_interval(interval: int):
    """기본 반복문으로 지정한 초마다 실행합니다."""

    while True:
        run_once()
        print(f"{interval}초 후 다시 실행합니다.")
        time.sleep(interval)


def run_with_schedule(seconds: int):
    """schedule 라이브러리로 지정한 초마다 실행합니다."""

    schedule.every(seconds).seconds.do(run_once)

    print(
        f"schedule 방식으로 {seconds}초마다 실행합니다."
    )

    # 기다리지 않고 첫 리포트를 바로 생성합니다.
    run_once()

    while True:
        schedule.run_pending()
        time.sleep(1)


def main():
    parser = argparse.ArgumentParser(
        description="매출 리포트 자동 생성"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=0,
        help="기본 반복 간격(초). 0이면 한 번만 실행",
    )

    parser.add_argument(
        "--schedule-seconds",
        type=int,
        help="schedule 라이브러리 반복 간격(초)",
    )

    args = parser.parse_args()

    if args.interval < 0:
        parser.error(
            "--interval은 0 이상의 숫자여야 합니다."
        )

    if (
        args.schedule_seconds is not None
        and args.schedule_seconds <= 0
    ):
        parser.error(
            "--schedule-seconds는 양수여야 합니다."
        )

    if args.schedule_seconds is not None:
        run_with_schedule(
            args.schedule_seconds
        )

    elif args.interval == 0:
        run_once()

    else:
        run_interval(
            args.interval
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n스케줄러를 종료했습니다.")