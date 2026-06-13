"""Configuração de logging do TaskGuard.

Implementa logging em múltiplos destinos:

* **Console** (stdout) — facilita observabilidade em containers (12-factor).
* **Arquivo rotativo** (`logs/taskguard.log`) — retenção local.
* **Arquivo de segurança** (`logs/security.log`) — eventos sensíveis
  (autenticação, falhas, tentativas suspeitas) num canal dedicado.
* **Syslog** — encaminhamento opcional para um coletor central (SIEM),
  habilitado por `SYSLOG_ENABLED`.

Um *logger* dedicado chamado ``security`` concentra os eventos de segurança,
no formato consumido pelos filtros do Fail2Ban (ver `monitoring/`).
"""
from __future__ import annotations

import logging
import socket
from logging.handlers import RotatingFileHandler, SysLogHandler
from pathlib import Path

from flask import Flask, has_request_context, request

# Nome do logger de segurança, referenciado em todo o código.
SECURITY_LOGGER_NAME = "security"

# Formato padrão das mensagens de segurança. É propositalmente estável e
# previsível para que os filtros do Fail2Ban consigam casar via regex.
SECURITY_FORMAT = (
    "%(asctime)s TASKGUARD-SECURITY %(levelname)s "
    "event=%(event)s ip=%(client_ip)s user=%(username)s detail=%(message)s"
)

APP_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


class RequestContextFilter(logging.Filter):
    """Injeta IP do cliente e usuário no registro de log, quando disponíveis.

    Garante que os campos `client_ip` e `username` sempre existam, evitando
    KeyError no formatter mesmo fora de um contexto de requisição.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "event"):
            record.event = "generic"
        if not hasattr(record, "username"):
            record.username = "-"
        if not hasattr(record, "client_ip"):
            if has_request_context():
                # Respeita proxies confiáveis (X-Forwarded-For tratado pelo
                # ProxyFix em create_app); cai para remote_addr caso contrário.
                record.client_ip = request.headers.get(
                    "X-Forwarded-For", request.remote_addr or "-"
                ).split(",")[0].strip()
            else:
                record.client_ip = "-"
        return True


def _build_syslog_handler(app: Flask) -> logging.Handler | None:
    """Cria o handler de syslog conforme a configuração do app."""
    host = app.config["SYSLOG_HOST"]
    port = app.config["SYSLOG_PORT"]
    try:
        # Em hosts Linux, /dev/log oferece syslog local sem rede.
        local_socket = Path("/dev/log")
        if host in {"localhost", "127.0.0.1"} and local_socket.exists():
            handler: logging.Handler = SysLogHandler(address=str(local_socket))
        else:
            handler = SysLogHandler(
                address=(host, port), socktype=socket.SOCK_DGRAM
            )
    except OSError as exc:  # noqa: BLE001 - falha tolerável
        app.logger.warning("Syslog indisponível (%s); seguindo sem ele.", exc)
        return None

    handler.setFormatter(logging.Formatter(SECURITY_FORMAT))
    handler.addFilter(RequestContextFilter())
    return handler


def configure_logging(app: Flask) -> None:
    """Configura todos os handlers de logging na aplicação."""
    log_dir: Path = app.config["LOG_DIR"]
    log_dir.mkdir(parents=True, exist_ok=True)
    level = getattr(logging, str(app.config["LOG_LEVEL"]).upper(), logging.INFO)

    context_filter = RequestContextFilter()

    # ------------------------------------------------------------------ #
    # Logger da aplicação (app.logger)
    # ------------------------------------------------------------------ #
    app.logger.handlers.clear()
    app.logger.setLevel(level)

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(APP_FORMAT))
    console.addFilter(context_filter)
    app.logger.addHandler(console)

    app_file = RotatingFileHandler(
        log_dir / "taskguard.log", maxBytes=1_000_000, backupCount=5, encoding="utf-8"
    )
    app_file.setFormatter(logging.Formatter(APP_FORMAT))
    app_file.addFilter(context_filter)
    app.logger.addHandler(app_file)

    # ------------------------------------------------------------------ #
    # Logger de segurança (dedicado)
    # ------------------------------------------------------------------ #
    security_logger = logging.getLogger(SECURITY_LOGGER_NAME)
    security_logger.handlers.clear()
    security_logger.setLevel(logging.INFO)
    security_logger.propagate = False  # Não duplica no logger raiz

    security_format = logging.Formatter(SECURITY_FORMAT)

    security_console = logging.StreamHandler()
    security_console.setFormatter(security_format)
    security_console.addFilter(context_filter)
    security_logger.addHandler(security_console)

    security_file = RotatingFileHandler(
        log_dir / "security.log", maxBytes=1_000_000, backupCount=10, encoding="utf-8"
    )
    security_file.setFormatter(security_format)
    security_file.addFilter(context_filter)
    security_logger.addHandler(security_file)

    if app.config.get("SYSLOG_ENABLED"):
        syslog_handler = _build_syslog_handler(app)
        if syslog_handler is not None:
            security_logger.addHandler(syslog_handler)
            app.logger.info("Encaminhamento para syslog habilitado.")

    app.logger.info("Subsistema de logging inicializado (nível=%s).", level)


def log_security_event(event: str, message: str, *, username: str = "-",
                       level: int = logging.INFO) -> None:
    """Registra um evento no canal de segurança.

    Parameters
    ----------
    event:
        Identificador curto do evento (ex.: ``login_success``,
        ``login_failed``, ``account_locked``, ``brute_force_suspected``).
    message:
        Detalhe textual livre do evento.
    username:
        Usuário associado, quando aplicável.
    level:
        Nível de severidade (``logging.INFO``, ``logging.WARNING`` …).
    """
    logger = logging.getLogger(SECURITY_LOGGER_NAME)
    logger.log(level, message, extra={"event": event, "username": username})
