"""Email tool — Gmail SMTP (send) + IMAP (poll for replies).

When GMAIL_APP_PASSWORD is not set, this module operates in `dry_run` mode:
send_email() returns a fake Message-ID, poll_inbox() returns an empty list,
and demos can be staged by injecting synthetic replies via `inject_reply()`.

This lets the orchestrator be exercised end-to-end without live email creds.
"""

from __future__ import annotations

import asyncio
import email
import email.utils
import logging
import re
import ssl
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
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
    from_display_name: Optional[str] = None,
    reply_to: Optional[str] = None,
) -> str:
    """Send an email via Gmail SMTP. Returns the SMTP Message-ID.

    The SMTP login is always settings.gmail_address (team mailbox).
    to_address is the prospect — never used as the sender.
    from_display_name / reply_to come from the campaign sales rep fields.
    """
    domain = (settings.gmail_address.split("@")[-1] if settings.gmail_address else "niaga.local")
    msg_id = email.utils.make_msgid(domain=domain)

    if _dry_run():
        log.warning(
            "[DRY-RUN] Would send FROM %s (display=%s) TO=%s reply_to=%s subject=%s",
            settings.gmail_address or "niaga",
            from_display_name,
            to_address,
            reply_to,
            subject,
        )
        return msg_id

    msg = EmailMessage()
    smtp_from = settings.gmail_address
    if from_display_name and smtp_from:
        msg["From"] = f"{from_display_name} <{smtp_from}>"
    else:
        msg["From"] = smtp_from
    if reply_to and reply_to.lower() != (smtp_from or "").lower():
        msg["Reply-To"] = reply_to
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

# Heuristics that mark where the quoted prior message starts. Trim everything
# from the match onward. Patterns are matched line-anchored, case-insensitive.
_QUOTE_BOUNDARIES = [
    re.compile(r"^On\s+.{4,120}wrote:\s*$", re.IGNORECASE),       # Gmail (EN)
    re.compile(r"^Pada\s+.{4,120}menulis:\s*$", re.IGNORECASE),   # Gmail (ID)
    re.compile(r"^-{2,}\s*Original Message\s*-{2,}\s*$", re.IGNORECASE),  # Outlook
    re.compile(r"^From:\s+.+$", re.IGNORECASE),                   # Outlook header block
    re.compile(r"^_{5,}\s*$"),                                    # underline divider
]


def _extract_plaintext(raw: bytes) -> str:
    """Parse a full RFC822 message and return the cleaned plain-text body.

    - Picks the text/plain part if present, else converts text/html to text.
    - Decodes quoted-printable / base64 transfer encoding.
    - Strips the quoted prior message and trailing `>` lines.
    """
    msg = email.message_from_bytes(raw)
    plain, html = None, None
    for part in msg.walk():
        if part.is_multipart():
            continue
        ctype = part.get_content_type()
        if ctype not in ("text/plain", "text/html"):
            continue
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        charset = part.get_content_charset() or "utf-8"
        try:
            decoded = payload.decode(charset, errors="replace")
        except (LookupError, TypeError):
            decoded = payload.decode("utf-8", errors="replace")
        if ctype == "text/plain" and plain is None:
            plain = decoded
        elif ctype == "text/html" and html is None:
            html = decoded

    body = plain
    if body is None and html is not None:
        body = re.sub(r"<[^>]+>", "", html)  # cheap tag strip
    if body is None:
        return ""

    # Cut at the first quote boundary we find.
    lines = body.splitlines()
    cut_at = len(lines)
    for i, ln in enumerate(lines):
        if any(p.match(ln.strip()) for p in _QUOTE_BOUNDARIES):
            cut_at = i
            break
    lines = lines[:cut_at]
    # Drop trailing blank lines and trailing `>` quote lines.
    while lines and (not lines[-1].strip() or lines[-1].lstrip().startswith(">")):
        lines.pop()
    return "\n".join(lines).strip()


def _header(msg: email.message.Message, name: str) -> str:
    value = msg.get(name, "")
    if not value:
        return ""
    # Decode RFC 2047 encoded-word headers (e.g. "=?UTF-8?Q?...?=")
    parts = email.header.decode_header(value)
    out = []
    for chunk, charset in parts:
        if isinstance(chunk, bytes):
            try:
                out.append(chunk.decode(charset or "utf-8", errors="replace"))
            except LookupError:
                out.append(chunk.decode("utf-8", errors="replace"))
        else:
            out.append(chunk)
    return "".join(out).strip()


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
        # Narrow to recent unread mail. A busy personal Gmail can have tens of
        # thousands of UNSEEN messages — fetching them all would blow the run's
        # lifetime without ever reaching the actual reply. Replies to outreach
        # arrive within hours, so a 2-day window catches them.
        since = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%d-%b-%Y")
        _, data = await client.search("UNSEEN", "SINCE", since)
        if not data:
            await client.logout()
            return []
        uids = data[0].decode().split()
        # Hard cap so a sudden flood can't lock up the poller.
        if len(uids) > 50:
            log.warning("poll_inbox: %d UNSEEN since %s, capping at 50 newest", len(uids), since)
            uids = uids[-50:]
        out: list[InboundReply] = []
        for uid in uids:
            _, raw = await client.fetch(uid, "(RFC822)")
            if not raw or len(raw) < 2:
                continue
            blob = raw[1] if isinstance(raw[1], (bytes, bytearray)) else raw[1].encode()
            msg = email.message_from_bytes(blob)
            body = _extract_plaintext(blob)
            out.append(
                InboundReply(
                    message_id=_header(msg, "Message-ID") or f"<imap-{uid}@niaga.local>",
                    in_reply_to=_header(msg, "In-Reply-To") or None,
                    from_address=_header(msg, "From"),
                    subject=_header(msg, "Subject"),
                    body=body,
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
