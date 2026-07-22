import json
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from urllib.request import Request, urlopen


def send_email(report_path: Path) -> None:
    """환경변수 설정이 있을 때 이메일 알림을 보냅니다."""

    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    email_to = os.getenv("EMAIL_TO")

    if not all([smtp_user, smtp_password, email_to]):
        print("이메일 설정이 없어 이메일 알림을 건너뜁니다.")
        return

    message = EmailMessage()
    message["Subject"] = "매출 리포트 생성 완료"
    message["From"] = smtp_user
    message["To"] = email_to
    message.set_content(
        f"새 매출 리포트가 생성되었습니다.\n\n"
        f"파일: {report_path.resolve()}"
    )

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(message)

    print("이메일 알림 전송 완료")


def send_slack(report_path: Path) -> None:
    """Slack Webhook이 설정돼 있을 때 알림을 보냅니다."""

    webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    if not webhook_url:
        print("Slack Webhook 설정이 없어 Slack 알림을 건너뜁니다.")
        return

    payload = {
        "text": (
            "📊 새 매출 리포트가 생성되었습니다.\n"
            f"파일: {report_path.resolve()}"
        )
    }

    request = Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=10):
        pass

    print("Slack 알림 전송 완료")


def send_notifications(report_path: Path) -> None:
    """이메일과 Slack 알림을 한 번에 처리합니다."""

    send_email(report_path)
    send_slack(report_path)