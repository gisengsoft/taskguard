"""Camada de segurança transversal do TaskGuard.

Reúne a configuração do Flask-Talisman (headers de segurança, CSP, HSTS) e
utilitários de sanitização de entrada usados pelos formulários e rotas.
"""
from __future__ import annotations

import html
import re

from flask import Flask
from markupsafe import Markup

from app.extensions import talisman

# Cabeçalhos de segurança adicionais aplicados a toda resposta. O Talisman já
# cuida de X-Frame-Options, X-Content-Type-Options, HSTS e CSP; aqui reforçamos
# políticas de referrer e permissões do navegador.
ADDITIONAL_SECURITY_HEADERS = {
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "X-Permitted-Cross-Domain-Policies": "none",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}


def init_security(app: Flask) -> None:
    """Inicializa o Talisman e registra os headers complementares."""
    talisman.init_app(
        app,
        force_https=app.config.get("FORCE_HTTPS", False),
        strict_transport_security=app.config.get("FORCE_HTTPS", False),
        strict_transport_security_max_age=31_536_000,  # 1 ano
        session_cookie_secure=app.config.get("SESSION_COOKIE_SECURE", False),
        content_security_policy=app.config.get("CONTENT_SECURITY_POLICY"),
        content_security_policy_nonce_in=["script-src"],
        frame_options="DENY",
        referrer_policy="strict-origin-when-cross-origin",
    )

    @app.after_request
    def _apply_extra_headers(response):  # type: ignore[no-untyped-def]
        for header, value in ADDITIONAL_SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response


# Padrão de caracteres de controle (exceto tab/newline) a serem removidos.
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_text(value: str | None, *, max_length: int | None = None) -> str:
    """Sanitiza texto livre vindo do usuário.

    Estratégia de defesa em profundidade contra XSS armazenado:

    1. Normaliza ``None`` para string vazia.
    2. Remove caracteres de controle não imprimíveis.
    3. Colapsa espaços em excesso e apara as bordas.
    4. Faz *escape* de entidades HTML (``<``, ``>``, ``&``, aspas).
    5. Opcionalmente trunca ao tamanho máximo.

    Observação: os templates Jinja2 já fazem auto-escape; esta função adiciona
    uma segunda barreira, útil para conteúdo persistido e reutilizado.
    """
    if value is None:
        return ""
    text = _CONTROL_CHARS.sub("", str(value))
    text = re.sub(r"\s+", " ", text).strip()
    text = html.escape(text, quote=True)
    if max_length is not None:
        text = text[:max_length]
    return text


def safe_render(value: str | None) -> Markup:
    """Marca texto previamente sanitizado como seguro para renderização."""
    return Markup(sanitize_text(value))
