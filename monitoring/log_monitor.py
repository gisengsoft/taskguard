#!/usr/bin/env python3
"""log_monitor.py — Monitor de segurança leve para o TaskGuard.

Alternativa multiplataforma ao Fail2Ban (útil onde ele não está disponível,
como em containers ou Windows). Faz *tail* do arquivo `security.log`, agrega
falhas de autenticação por IP em janelas de tempo e emite alertas quando um
limiar é ultrapassado — sinal típico de ataque de força bruta.

Uso:
    python monitoring/log_monitor.py
    python monitoring/log_monitor.py --logfile logs/security.log --threshold 5 --window 60

Saída: alertas no console e gravados em `logs/alerts.log`. Os IPs suspeitos
são exibidos para que um operador (ou um hook de firewall) possa agir.
"""
from __future__ import annotations

import argparse
import logging
import re
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

# Casa as linhas de falha emitidas pelo logger de segurança da aplicação.
FAILURE_PATTERN = re.compile(
    r"TASKGUARD-SECURITY\s+\S+\s+event=(?P<event>login_failed|account_locked|"
    r"rate_limit_exceeded|idor_attempt)\s+ip=(?P<ip>\S+)\s+user=(?P<user>\S+)"
)

# Eventos que contam como "tentativa suspeita".
SUSPICIOUS_EVENTS = {
    "login_failed", "account_locked", "rate_limit_exceeded", "idor_attempt",
}


def _build_alert_logger(alert_path: Path) -> logging.Logger:
    """Logger dedicado para os alertas gerados pelo monitor."""
    logger = logging.getLogger("taskguard.monitor")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        fmt = logging.Formatter("%(asctime)s ALERT %(message)s")
        console = logging.StreamHandler()
        console.setFormatter(fmt)
        logger.addHandler(console)
        alert_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(alert_path, encoding="utf-8")
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
    return logger


def _follow(path: Path):
    """Gerador que faz *tail -f* de um arquivo, tolerando rotação/ausência."""
    while not path.exists():
        print(f"[monitor] Aguardando o arquivo de log: {path} ...")
        time.sleep(2)

    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        handle.seek(0, 2)  # vai para o fim do arquivo
        while True:
            line = handle.readline()
            if not line:
                time.sleep(0.4)
                # Detecta rotação (arquivo truncado/recriado).
                try:
                    if handle.tell() > path.stat().st_size:
                        handle.seek(0)
                except FileNotFoundError:
                    time.sleep(1)
                continue
            yield line


def monitor(logfile: Path, threshold: int, window: int, alert_path: Path) -> None:
    """Loop principal de monitoramento."""
    alert_logger = _build_alert_logger(alert_path)
    # Para cada IP, mantém uma fila de timestamps das falhas recentes.
    attempts: dict[str, deque[float]] = defaultdict(deque)
    alerted_until: dict[str, float] = {}

    print(f"[monitor] Vigiando {logfile} | limiar={threshold} falhas / {window}s")
    for line in _follow(logfile):
        match = FAILURE_PATTERN.search(line)
        if not match:
            continue
        event = match.group("event")
        if event not in SUSPICIOUS_EVENTS:
            continue

        ip = match.group("ip")
        user = match.group("user")
        now = time.time()

        bucket = attempts[ip]
        bucket.append(now)
        # Descarta o que saiu da janela de observação.
        while bucket and now - bucket[0] > window:
            bucket.popleft()

        if len(bucket) >= threshold and alerted_until.get(ip, 0) < now:
            stamp = datetime.now(timezone.utc).isoformat()
            alert_logger.warning(
                "POSSIVEL BRUTE FORCE ip=%s falhas=%d janela=%ss usuario_alvo=%s ts=%s",
                ip, len(bucket), window, user, stamp,
            )
            # Evita spam de alertas para o mesmo IP por uma janela.
            alerted_until[ip] = now + window


def main() -> None:
    parser = argparse.ArgumentParser(description="Monitor de segurança do TaskGuard.")
    parser.add_argument("--logfile", default="logs/security.log",
                        help="caminho do arquivo de log de segurança")
    parser.add_argument("--threshold", type=int, default=5,
                        help="nº de falhas que dispara o alerta")
    parser.add_argument("--window", type=int, default=60,
                        help="janela de observação em segundos")
    parser.add_argument("--alertfile", default="logs/alerts.log",
                        help="arquivo onde os alertas serão gravados")
    args = parser.parse_args()

    try:
        monitor(Path(args.logfile), args.threshold, args.window, Path(args.alertfile))
    except KeyboardInterrupt:
        print("\n[monitor] Encerrado.")


if __name__ == "__main__":
    main()
