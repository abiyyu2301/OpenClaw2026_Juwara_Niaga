"""Email tool — Gmail SMTP (send) + IMAP (poll for replies).

When GMAIL_APP_PASSWORD is not set, this module operates in `dry_run` mode:
send_email() returns a fake Message-ID, poll_inbox() returns an empty list,
and demos can be staged by injecting synthetic replies via `inject_reply()`.

This lets the orchestrator be exercised end-to-end without live email creds.
"""

from __future__ import annotations

import asyncio
import email.utils
import logging
import re
import ssl
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import List, Optional

from settings import settings

log = logging.getLogger(__name__)


@dataclass
class InboundReply:
    message_id: str
    in_reply_to: Optional[str]
    from_address: str
    subject: str
    body: str
    received_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ---- send (SMTP) --------------------------------------------------------

def _dry_run() -> bool:
    return not (settings.gmail_address and settings.gmail_app_password)


async def send_email(
    *,
    to_address: str,
    subject: str,
    body: str,
    in_reply_to: Optional[str] = None,
) -> str:
    """Send an email via Gmail SMTP. Returns the SMTP Message-ID.

    In dry-run mode (no Gmail credentials), logs the would-be email and
    returns a fake Message-ID so downstream code can store something.
    """
    domain = (settings.gmail_address.split("@")[-1] if settings.gmail_address else "niaga.local")
    msg_id = email.utils.make_msgid(domain=domain)

    if _dry_run():
        log.warning(
            "[DRY-RUN] Would send email to=%s subject=%s body_len=%d",
            to_address, subject, len(body),
        )
        return msg_id

    msg = EmailMessage()
    msg["From"] = settings.gmail_address
    msg["To"] = to_address
    msg["Subject"] = subject
    msg["Message-ID"] = msg_id
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to
    msg.set_content(body)

    # Use aiosmtplib for non-blocking send
    import aiosmtplib

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        start_tls=True,
        username=settings.gmail_address,
        password=settings.gmail_app_password,
        tls_context=ssl.create_default_context(),
        timeout=30,
    )
    log.info("Sent email to %s (msg-id=%s)", to_address, msg_id)
    return msg_id


# ---- receive (IMAP) -----------------------------------------------------

_RE_MID = re.compile(r"Message-ID:\s*(<[^>]+>)", re.IGNORECASE)
_RE_IRT = re.compile(r"In-Reply-To:\s*(<[^>]+>)", re.IGNORECASE)
_RE_FROM = re.compile(r"From:\s*(.+)", re.IGNORECASE)
_RE_SUBJECT = re.compile(r"Subject:\s*(.+)", re.IGNORECASE)


# Synthetic-reply queue for dry-run mode / pre-staged demo
_synthetic_queue: list[InboundReply] = []


def inject_reply(
    *,
    from_address: str,
    subject: str,
    body: str,
    in_reply_to: Optional[str] = None,
) -> InboundReply:
    """Stage a reply in the dry-run inbox. The next poll_inbox() call will
    return it (and only it)."""
    reply = InboundReply(
        message_id=f"<{uuid.uuid4()}@niaga.local>",
        in_reply_to=in_reply_to,
        from_address=from_address,
        subject=subject,
        body=body,
    )
    _synthetic_queue.append(reply)
    return reply


async def poll_inbox(*, since_uid: int = 0) -> List[InboundReply]:
    """Fetch new replies from the IMAP inbox.

    Returns inbound replies received since the last poll. In dry-run mode,
    returns whatever has been injected via inject_reply().
    """
    if _dry_run():
        if not _synthetic_queue:
            return []
        out, _synthetic_queue[:] = list(_synthetic_queue), []
        return out

    import aioimaplib

    try:
        client = aioimaplib.IMAP4_SSL(
            host=settings.imap_host,
            port=settings.imap_port,
            timeout=15,
        )
        await client.wait_hello_from_server()
        await client.login(settings.gmail_address, settings.gmail_app_password)
        await client.select("INBOX")
        _, data = await client.search("UNSEEN")
        if not data:
            await client.logout()
            return []
        uids = data[0].decode().split()
        out: list[InboundReply] = []
        for uid in uids:
            _, raw = await client.fetch(uid, "(RFC822)")
            if not raw or len(raw) < 2:
                continue
            blob = raw[1] if isinstance(raw[1], (bytes, bytearray)) else raw[1].encode()
            text = blob.decode("utf-8", errors="replace")
            mid = _RE_MID.search(text)
            irt = _RE_IRT.search(text)
            frm = _RE_FROM.search(text)
            sub = _RE_SUBJECT.search(text)
            # crude body extraction: text after the first blank line
            sep = text.find("\r\n\r\n")
            body = text[sep + 4 :] if sep != -1 else text
            out.append(
                InboundReply(
                    message_id=mid.group(1) if mid else f"<imap-{uid}@niaga.local>",
                    in_reply_to=irt.group(1) if irt else None,
                    from_address=(frm.group(1).strip() if frm else "").strip(),
                    subject=(sub.group(1).strip() if sub else "").strip(),
                    body=body.strip(),
                )
            )
            await client.store(uid, "+FLAGS", "\\Seen")
        await client.logout()
        return out
    except Exception as exc:
        log.warning("IMAP poll failed: %s", exc)
        return []


# Backward-compatible exports
__all__ = ["InboundReply", "send_email", "poll_inbox", "inject_reply"]
