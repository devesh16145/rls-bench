"""Postgres lifecycle: pick a backend, keep one server up, build the template database."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from urllib.parse import quote

import psycopg

ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = Path(os.environ.get("RLS_STATE_DIR", ROOT / ".rlsbench"))
SHIM_PATH = Path(__file__).with_name("shim.sql")
TEMPLATE_DB = "rlsbench_template"

DOCKER_CONTAINER = "rlsbench-pg"
DOCKER_PORT = 54329
DOCKER_PASSWORD = "rlsbench"
PGCTL_PORT = 54330

CONNECT_OPTIONS = "-c TimeZone=UTC -c client_min_messages=warning"


def _docker_available() -> bool:
    if not shutil.which("docker"):
        return False
    probe = subprocess.run(["docker", "info"], capture_output=True)
    return probe.returncode == 0


def _pgserver_available() -> bool:
    try:
        import pgserver  # noqa: F401
    except ImportError:
        return False
    return True


def choose_backend() -> str:
    """docker → pgserver → pg_ctl, unless RLS_DB_BACKEND forces one."""
    forced = os.environ.get("RLS_DB_BACKEND")
    if forced:
        if forced not in {"docker", "pgserver", "pgctl"}:
            raise ValueError(f"unknown RLS_DB_BACKEND={forced!r}")
        return forced
    if _docker_available():
        return "docker"
    if _pgserver_available():
        return "pgserver"
    if shutil.which("pg_ctl"):
        return "pgctl"
    raise RuntimeError("no Postgres backend: install Docker, the pgserver package, or postgresql (pg_ctl)")


def _uri_file() -> Path:
    return STATE_DIR / "uri"


def _start_docker() -> str:
    running = subprocess.run(
        ["docker", "ps", "-q", "-f", f"name=^{DOCKER_CONTAINER}$"], capture_output=True, text=True
    ).stdout.strip()
    if not running:
        subprocess.run(["docker", "rm", "-f", DOCKER_CONTAINER], capture_output=True)
        subprocess.run(
            [
                "docker", "run", "-d", "--name", DOCKER_CONTAINER,
                "-e", f"POSTGRES_PASSWORD={DOCKER_PASSWORD}",
                "-p", f"{DOCKER_PORT}:5432", "postgres:16",
            ],
            check=True,
            capture_output=True,
        )
    return f"postgresql://postgres:{DOCKER_PASSWORD}@localhost:{DOCKER_PORT}/postgres"


def _start_pgserver() -> str:
    import pgserver

    server = pgserver.get_server(STATE_DIR / "pgdata", cleanup_mode=None)
    return server.get_uri()


def _start_pgctl() -> str:
    data = STATE_DIR / "pgdata-pgctl"
    sock = STATE_DIR / "sock"
    sock.mkdir(parents=True, exist_ok=True)
    if not (data / "PG_VERSION").exists():
        subprocess.run(
            ["initdb", "-D", str(data), "-U", "postgres", "--auth=trust", "-E", "UTF8"],
            check=True,
            capture_output=True,
        )
    status = subprocess.run(["pg_ctl", "-D", str(data), "status"], capture_output=True)
    if status.returncode != 0:
        subprocess.run(
            [
                "pg_ctl", "-D", str(data), "-w", "-l", str(STATE_DIR / "pgctl.log"),
                "-o", f"-p {PGCTL_PORT} -k {sock} -c listen_addresses=''",
                "start",
            ],
            check=True,
            capture_output=True,
        )
    return f"postgresql://postgres@/postgres?host={quote(str(sock))}&port={PGCTL_PORT}"


def _wait_ready(uri: str, timeout_s: float = 60.0) -> None:
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            with psycopg.connect(uri, connect_timeout=3):
                return
        except psycopg.OperationalError:
            if time.monotonic() > deadline:
                raise
            time.sleep(0.5)


def up() -> str:
    """Start (or reuse) the server, build the template, return the admin URI."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    backend = choose_backend()
    starter = {"docker": _start_docker, "pgserver": _start_pgserver, "pgctl": _start_pgctl}[backend]
    uri = starter()
    _wait_ready(uri)
    _uri_file().write_text(f"{backend}\n{uri}\n")
    ensure_template(uri)
    return uri


def down() -> None:
    if not _uri_file().exists():
        return
    backend = _uri_file().read_text().splitlines()[0]
    if backend == "docker":
        subprocess.run(["docker", "rm", "-f", DOCKER_CONTAINER], capture_output=True)
    elif backend == "pgserver":
        import pgserver

        pgserver.pg_ctl(["-D", str(STATE_DIR / "pgdata"), "-m", "fast", "stop"])
    elif backend == "pgctl":
        subprocess.run(["pg_ctl", "-D", str(STATE_DIR / "pgdata-pgctl"), "-m", "fast", "stop"], capture_output=True)
    _uri_file().unlink()


def admin_uri() -> str:
    """URI of the maintenance database; starts the server on first use."""
    if _uri_file().exists():
        uri = _uri_file().read_text().splitlines()[1]
        try:
            with psycopg.connect(uri, connect_timeout=3):
                return uri
        except psycopg.OperationalError:
            pass
    return up()


def uri_for(admin: str, dbname: str) -> str:
    # replace the path component (database name) of the admin URI
    head, sep, tail = admin.partition("?")
    base = head.rsplit("/", 1)[0]
    return f"{base}/{dbname}{sep}{tail}"


def connect(uri: str) -> psycopg.Connection:
    return psycopg.connect(uri, autocommit=True, options=CONNECT_OPTIONS, prepare_threshold=None)


def _shim_hash() -> str:
    return hashlib.sha256(SHIM_PATH.read_bytes()).hexdigest()[:16]


def ensure_template(admin: str) -> None:
    """(Re)build rlsbench_template when missing or when shim.sql changed."""
    wanted = _shim_hash()
    with connect(admin) as conn:
        row = conn.execute(
            "select shobj_description(oid, 'pg_database') from pg_database where datname = %s",
            [TEMPLATE_DB],
        ).fetchone()
        if row is not None and row[0] == wanted:
            return
        if row is not None:
            conn.execute(f"drop database {TEMPLATE_DB} with (force)")
        conn.execute(f"create database {TEMPLATE_DB}")
    with connect(uri_for(admin, TEMPLATE_DB)) as conn:
        conn.execute(SHIM_PATH.read_text())
        conn.execute(f"comment on database {TEMPLATE_DB} is '{wanted}'")


@contextmanager
def scratch_database() -> Iterator[str]:
    """Clone the template into a throwaway database; yield its URI; drop it afterwards."""
    admin = admin_uri()
    name = f"run_{uuid.uuid4().hex[:16]}"
    with connect(admin) as conn:
        conn.execute(f"create database {name} template {TEMPLATE_DB}")
    try:
        yield uri_for(admin, name)
    finally:
        with connect(admin) as conn:
            conn.execute(f"drop database if exists {name} with (force)")
