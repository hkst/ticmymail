import os
import smtplib
from email.message import EmailMessage
from typing import Dict


class EmailSendError(RuntimeError):
    pass


class EmailProvider:
    def __init__(self, config: Dict):
        self.config = config

    def _build_message(self, payload: Dict) -> EmailMessage:
        if "message_id" not in payload or "thread_id" not in payload:
            raise EmailSendError("message_id and thread_id are required")

        msg = EmailMessage()
        msg["Subject"] = payload.get("subject", "")
        msg["From"] = payload["from"]
        msg["To"] = payload["to"]
        msg["Message-ID"] = payload["message_id"]
        msg["In-Reply-To"] = payload.get("message_id")
        msg["References"] = payload.get("thread_id")
        msg.set_content(payload.get("body", ""))

        return msg

    def send(self, payload: Dict) -> Dict:
        provider_type = self.config.get("type", "smtp").lower()

        if provider_type == "smtp":
            return self._send_smtp(payload)
        if provider_type == "graph":
            raise EmailSendError("Graph provider not implemented in this reference implementation")
        if provider_type == "mock":
            msg = self._build_message(payload)
            return {
                "status": "sent",
                "provider": "mock",
                "from": msg["From"],
                "to": msg["To"],
                "message_id": payload["message_id"],
                "thread_id": payload["thread_id"],
            }

        raise EmailSendError(f"Unsupported email provider type: {provider_type}")

    def _send_smtp(self, payload: Dict) -> Dict:
        msg = self._build_message(payload)
        smtp_cfg = self.config.get("smtp", {})
        host = smtp_cfg.get("host", "localhost")
        port = int(smtp_cfg.get("port", 25))
        username = smtp_cfg.get("username")
        password = smtp_cfg.get("password")
        use_tls = bool(smtp_cfg.get("use_tls", True))

        with smtplib.SMTP(host, port, timeout=10) as smtp:
            if use_tls:
                smtp.starttls()
            if username and password:
                smtp.login(username, password)
            smtp.send_message(msg)

        return {
            "status": "sent",
            "provider": "smtp",
            "message_id": payload["message_id"],
            "thread_id": payload["thread_id"],
        }
