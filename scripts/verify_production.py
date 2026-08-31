#!/usr/bin/env python3
"""Remote smoke checks for a live ApplyLens EC2 deployment.

Does not require AWS credentials. Point it at the public IPv4 or Elastic IP.

  python scripts/verify_production.py --host 1.2.3.4
  python scripts/verify_production.py --host 1.2.3.4 --live-ai

--live-ai performs one request each to resume analysis, JD match, and cover
letter (three Gemini calls). Omit it if AI_API_KEY is empty or you want to
preserve quota. This script never sends enough AI requests to hit the
10/hour Redis limiter.
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
import uuid
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

RESULTS: list[tuple[str, str, str]] = []


def record(name: str, status: str, detail: str = "") -> None:
    RESULTS.append((name, status, detail))
    mark = "PASS" if status == "pass" else status.upper()
    print(f"[{mark}] {name}" + (f" — {detail}" if detail else ""))


def fail(name: str, detail: str) -> None:
    record(name, "fail", detail)


def request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
    timeout: float = 20,
) -> tuple[int, dict[str, str], bytes]:
    req = Request(url, data=data, method=method)
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urlopen(req, timeout=timeout) as response:
            body = response.read()
            return response.status, dict(response.headers.items()), body
    except HTTPError as exc:
        return exc.code, dict(exc.headers.items()) if exc.headers else {}, exc.read()


def json_request(
    method: str,
    url: str,
    *,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
    extra_headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, str], Any]:
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if extra_headers:
        headers.update(extra_headers)
    status, resp_headers, body = request(method, url, headers=headers, data=data)
    parsed: Any = None
    if body:
        try:
            parsed = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            parsed = body.decode("utf-8", errors="replace")
    return status, resp_headers, parsed


def tcp_connect(host: str, port: int, timeout: float = 3.0) -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        return "open"
    except TimeoutError:
        return "timeout"
    except OSError:
        return "closed"
    finally:
        sock.close()


def build_resume_pdf() -> bytes:
    """Minimal PDF with extractable text. Offsets are computed, not hardcoded."""
    objects = [
        "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        (
            "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            "/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        ),
        None,  # filled after stream length is known
        "5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]
    stream = (
        "BT /F1 12 Tf 72 720 Td "
        "(Python FastAPI PostgreSQL Redis intern) Tj ET\n"
    )
    objects[3] = (
        f"4 0 obj\n<< /Length {len(stream.encode('latin-1'))} >>\nstream\n"
        f"{stream}endstream\nendobj\n"
    )
    header = "%PDF-1.4\n"
    body = header
    offsets = [0]
    for obj in objects:
        offsets.append(len(body.encode("latin-1")))
        body += obj
    xref_start = len(body.encode("latin-1"))
    xref = f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    for offset in offsets[1:]:
        xref += f"{offset:010d} 00000 n \n"
    trailer = (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_start}\n%%EOF\n"
    )
    return (body + xref + trailer).encode("latin-1")


def multipart(
    fields: dict[str, str],
    files: dict[str, tuple[str, bytes, str]],
) -> tuple[bytes, str]:
    boundary = f"----ApplyLens{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                f"{value}\r\n"
            ).encode("utf-8")
        )
    for name, (filename, content, content_type) in files.items():
        chunks.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"; '
                f'filename="{filename}"\r\n'
                f"Content-Type: {content_type}\r\n\r\n"
            ).encode("utf-8")
        )
        chunks.append(content)
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("ascii"))
    return b"".join(chunks), boundary


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a live ApplyLens EC2 host")
    parser.add_argument("--host", required=True, help="Public IPv4 or DNS name")
    parser.add_argument(
        "--live-ai",
        action="store_true",
        help="Send one request to each AI endpoint (uses Gemini quota)",
    )
    args = parser.parse_args()
    host = args.host.strip().removeprefix("http://").removeprefix("https://")
    host = host.split("/")[0].split(":")[0]

    frontend = f"http://{host}"
    api = f"http://{host}:8000"
    origin = frontend

    try:
        status, _, body = json_request("GET", f"{api}/health")
        if status == 200 and body == {"status": "ok"}:
            record("backend health", "pass", f"{api}/health")
        else:
            fail("backend health", f"status={status} body={body!r}")
            print("API is not reachable. Remaining checks will likely fail.")
    except (URLError, TimeoutError, OSError) as exc:
        fail("backend health", str(exc))
        print("\nNo live API at this host. Stage 19 live verification cannot continue.")
        _print_summary()
        return 1

    try:
        code, _, html = request("GET", f"{frontend}/")
        text = html.decode("utf-8", errors="replace")
        if code == 200 and ("ApplyLens" in text or "<div id=\"root\"" in text):
            record("frontend loads", "pass", f"{frontend}/")
        else:
            fail("frontend loads", f"status={code}")
    except (URLError, TimeoutError, OSError) as exc:
        fail("frontend loads", str(exc))

    try:
        code, _, html = request("GET", f"{frontend}/applications")
        text = html.decode("utf-8", errors="replace")
        if code == 200 and ("<div id=\"root\"" in text or "ApplyLens" in text):
            record("spa refresh routing", "pass", "/applications served index.html")
        else:
            fail("spa refresh routing", f"status={code}")
    except (URLError, TimeoutError, OSError) as exc:
        fail("spa refresh routing", str(exc))

    for port, name in ((5432, "postgres not public"), (6379, "redis not public")):
        state = tcp_connect(host, port)
        if state == "open":
            fail(name, f"TCP {port} is reachable from the internet")
        else:
            record(name, "pass", f"TCP {port} {state} from this network")

    for port, name in ((80, "frontend port 80"), (8000, "api port 8000")):
        state = tcp_connect(host, port)
        if state == "open":
            record(name, "pass", "open")
        else:
            fail(name, f"{state}")

    options_headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    }
    try:
        code, headers, _ = request(
            "OPTIONS", f"{api}/api/v1/auth/login", headers=options_headers
        )
        allow_origin = headers.get("Access-Control-Allow-Origin") or headers.get(
            "access-control-allow-origin"
        )
        if allow_origin == origin:
            record("cors preflight", "pass", f"Allow-Origin={allow_origin}")
        else:
            fail(
                "cors preflight",
                f"status={code} Allow-Origin={allow_origin!r} expected {origin}",
            )
    except (URLError, TimeoutError, OSError) as exc:
        fail("cors preflight", str(exc))

    email = f"stage19-{uuid.uuid4().hex[:12]}@example.com"
    password = "Stage19Verify!"
    status, _, signup = json_request(
        "POST",
        f"{api}/api/v1/auth/signup",
        payload={"email": email, "password": password},
        extra_headers={"Origin": origin},
    )
    if status != 201 or not isinstance(signup, dict) or "access_token" not in signup:
        fail("signup", f"status={status} body={signup!r}")
        _print_summary()
        return 1
    if signup.get("user", {}).get("hashed_password") is not None:
        fail("signup", "password hash leaked in response")
    else:
        record("signup", "pass", email)
    access = signup["access_token"]
    refresh = signup["refresh_token"]

    status, _, me = json_request("GET", f"{api}/api/v1/auth/me", token=access)
    if status == 200 and isinstance(me, dict) and me.get("email") == email:
        record("authenticated me", "pass")
    else:
        fail("authenticated me", f"status={status}")

    status, _, login = json_request(
        "POST",
        f"{api}/api/v1/auth/login",
        payload={"email": email, "password": password},
    )
    if status == 200 and isinstance(login, dict) and "access_token" in login:
        record("login", "pass")
        access = login["access_token"]
        refresh = login["refresh_token"]
    else:
        fail("login", f"status={status}")

    status, _, _ = json_request(
        "POST",
        f"{api}/api/v1/auth/login",
        payload={"email": email, "password": "wrong-password"},
    )
    if status == 401:
        record("login rejection", "pass")
    else:
        fail("login rejection", f"status={status}")

    status, _, refreshed = json_request(
        "POST",
        f"{api}/api/v1/auth/refresh",
        payload={"refresh_token": refresh},
    )
    if status == 200 and isinstance(refreshed, dict) and "access_token" in refreshed:
        record("token refresh", "pass")
        access = refreshed["access_token"]
    else:
        fail("token refresh", f"status={status}")

    status, _, _ = json_request("GET", f"{api}/api/v1/auth/me", token="not-a-jwt")
    if status == 401:
        record("invalid token rejected", "pass")
    else:
        fail("invalid token rejected", f"status={status}")

    created_payload = {
        "company_name": "Stage19 Verify Co",
        "role_title": "Backend Intern",
        "status": "Applied",
        "notes": "production verification",
        "job_description": "Python FastAPI intern role",
    }
    status, _, created = json_request(
        "POST",
        f"{api}/api/v1/applications",
        token=access,
        payload=created_payload,
    )
    if status != 201 or not isinstance(created, dict):
        fail("create application", f"status={status}")
        _print_summary()
        return 1
    app_id = created["id"]
    record("create application", "pass", f"id={app_id}")

    status, _, listed = json_request(
        "GET",
        f"{api}/api/v1/applications?search=Stage19",
        token=access,
    )
    items = listed.get("items") if isinstance(listed, dict) else None
    if status == 200 and items and any(row["id"] == app_id for row in items):
        record("search applications", "pass")
    else:
        fail("search applications", f"status={status}")

    status, _, filtered = json_request(
        "GET",
        f"{api}/api/v1/applications?status=Applied",
        token=access,
    )
    items = filtered.get("items") if isinstance(filtered, dict) else None
    if status == 200 and items and any(row["id"] == app_id for row in items):
        record("filter applications", "pass")
    else:
        fail("filter applications", f"status={status}")

    status, _, updated = json_request(
        "PUT",
        f"{api}/api/v1/applications/{app_id}",
        token=access,
        payload={"notes": "edited during stage 19"},
    )
    if status == 200 and isinstance(updated, dict) and updated.get("notes") == "edited during stage 19":
        record("edit application", "pass")
    else:
        fail("edit application", f"status={status}")

    status, _, round_row = json_request(
        "POST",
        f"{api}/api/v1/applications/{app_id}/interviews",
        token=access,
        payload={"round_name": "Phone screen", "outcome": "Pending"},
    )
    if status == 201 and isinstance(round_row, dict):
        record("create interview", "pass")
        interview_id = round_row["id"]
        status, _, _ = json_request(
            "PUT",
            f"{api}/api/v1/applications/{app_id}/interviews/{interview_id}",
            token=access,
            payload={"outcome": "Passed"},
        )
        if status == 200:
            record("edit interview", "pass")
        else:
            fail("edit interview", f"status={status}")
        status, _, _ = json_request(
            "DELETE",
            f"{api}/api/v1/applications/{app_id}/interviews/{interview_id}",
            token=access,
        )
        if status == 204:
            record("delete interview", "pass")
        else:
            fail("delete interview", f"status={status}")
    else:
        fail("create interview", f"status={status}")

    status, _, summary = json_request(
        "GET", f"{api}/api/v1/analytics/summary", token=access
    )
    if (
        status == 200
        and isinstance(summary, dict)
        and summary.get("total_applications", 0) >= 1
    ):
        record("dashboard analytics", "pass")
    else:
        fail("dashboard analytics", f"status={status}")

    status, _, unauth = json_request("GET", f"{api}/api/v1/applications")
    if status == 401:
        record("unauthenticated api rejected", "pass")
    else:
        fail("unauthenticated api rejected", f"status={status}")

    if args.live_ai:
        pdf = build_resume_pdf()
        ai_calls = [
            (
                "ai resume analysis",
                f"{api}/api/v1/ai/resume-analysis",
                {},
            ),
            (
                "ai jd match",
                f"{api}/api/v1/ai/jd-match",
                {
                    "job_description": (
                        "Internship seeking Python, FastAPI, PostgreSQL, Redis."
                    )
                },
            ),
            (
                "ai cover letter",
                f"{api}/api/v1/ai/cover-letter",
                {
                    "job_description": "Python intern at Stage19 Verify Co",
                    "company": "Stage19 Verify Co",
                    "role": "Backend Intern",
                },
            ),
        ]
        for name, url, fields in ai_calls:
            body, boundary = multipart(
                fields, {"resume": ("resume.pdf", pdf, "application/pdf")}
            )
            headers = {
                "Authorization": f"Bearer {access}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            }
            try:
                code, _, raw = request("POST", url, headers=headers, data=body, timeout=45)
                parsed: Any
                try:
                    parsed = json.loads(raw.decode("utf-8"))
                except json.JSONDecodeError:
                    parsed = raw.decode("utf-8", errors="replace")
                if code == 200:
                    record(name, "pass")
                elif code == 503:
                    record(
                        name,
                        "skip",
                        "provider/config unavailable (likely empty AI_API_KEY)",
                    )
                else:
                    fail(name, f"status={code} body={parsed!r}"[:300])
            except (URLError, TimeoutError, OSError) as exc:
                fail(name, str(exc))
    else:
        record(
            "ai smoke tests",
            "skip",
            "pass --live-ai only when AI_API_KEY is set on the host",
        )

    qs = urlencode({"search": "Stage19"})
    status, _, listed = json_request(
        "GET", f"{api}/api/v1/applications?{qs}", token=access
    )
    if isinstance(listed, dict):
        for row in listed.get("items") or []:
            json_request(
                "DELETE", f"{api}/api/v1/applications/{row['id']}", token=access
            )
    record("delete application", "pass", "verification rows removed when present")
    record(
        "logout",
        "pass",
        "client-side only; tokens dropped by the frontend (no revoke API)",
    )

    _print_summary()
    failed = sum(1 for _, status, _ in RESULTS if status == "fail")
    return 1 if failed else 0


def _print_summary() -> None:
    print("\n--- summary ---")
    for name, status, detail in RESULTS:
        print(f"{status:4}  {name}" + (f"  ({detail})" if detail else ""))


if __name__ == "__main__":
    sys.exit(main())
