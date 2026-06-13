# Política de Segurança

## Versões suportadas

| Versão | Suporte de segurança |
|--------|----------------------|
| 1.0.x  | ✅ Sim               |

## Como reportar uma vulnerabilidade

Encontrou um problema de segurança? **Não abra uma *issue* pública.**

1. Envie os detalhes de forma privada ao mantenedor (e-mail/contato no perfil do autor).
2. Inclua: descrição, passos de reprodução, impacto estimado e, se possível, uma sugestão de correção.
3. Você receberá uma confirmação de recebimento em até 72 horas e atualizações sobre a correção.

## Defesas implementadas

Este projeto adota *security by design*. Entre os controles ativos:

- Autenticação com *hash* PBKDF2-SHA256 e proteção contra força bruta (rate limiting + bloqueio de conta).
- Proteção CSRF em todos os formulários (Flask-WTF).
- Defesa contra XSS (auto-escape + sanitização + CSP estrita com *nonce*).
- Prevenção de SQL Injection via ORM (consultas parametrizadas).
- Controle de acesso por proprietário (anti-IDOR).
- Cabeçalhos de segurança e HSTS (Flask-Talisman).
- Verificação contínua na pipeline: **SAST** (Bandit), **SCA** (OWASP Dependency-Check) e **DAST** (OWASP ZAP).

## Verificação local

```bash
./scripts/run_sast.sh                 # análise estática
./scripts/run_dependency_check.sh     # análise de dependências (CVE)
./scripts/run_dast.sh                 # análise dinâmica
```
