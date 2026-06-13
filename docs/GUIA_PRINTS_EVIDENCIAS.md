# Guia de Prints e Evidências — TaskGuard (Entrega Acadêmica)

Checklist estratégico das capturas de tela que comprovam o projeto. A ideia é
**contar uma história técnica**: aplicação funcionando → containerização →
banco → automação → segurança → testes. Cada print abaixo indica **o que ele
comprova** academicamente.

> Você **não** precisa de todos. A coluna **Prioridade** marca os
> **obrigatórios** (★★★), os que **impressionam** a banca (★★) e os
> **complementares** (★).

---

## Como usar este guia

1. Siga a **ordem recomendada** (seção 1) — ela cria uma narrativa coerente.
2. Capture os prints com boa resolução (janela maximizada, texto legível).
3. **Anonimize segredos**: borre senhas reais, tokens e chaves antes de entregar.
4. Encaixe os 4 prints principais nas **molduras do relatório**
   (`docs/relatorio_academico.tex`, seção *Evidências*) — veja o mapeamento na
   seção 4. Os demais podem ir em um apêndice.

---

## 1. Ordem recomendada de captura (a narrativa)

| # | Print | Comando/Tela | Prioridade |
|---|---|---|---|
| 1 | Containers no ar | `docker compose ps` / `docker ps` | ★★★ |
| 2 | Tela de login | <http://localhost:8000> | ★★★ |
| 3 | Painel de tarefas (logado) | dashboard após login `demo` | ★★★ |
| 4 | CRUD funcionando | criar/editar/concluir uma tarefa | ★★ |
| 5 | Health check | `curl http://localhost:8000/health` → 200 | ★★ |
| 6 | pgAdmin conectado + tabelas | pgAdmin → tabelas `users`/`tasks` | ★★★ |
| 7 | Registros no banco | View/Edit Data de `users` e `tasks` | ★★ |
| 8 | pytest + cobertura | `pytest --cov=app` | ★★★ |
| 9 | flake8 sem erros | `flake8 app run.py config.py` | ★ |
| 10 | Bandit (SAST) | `bandit -r app ...` saída limpa | ★★★ |
| 11 | Dependency-Check (SCA) | relatório HTML gerado | ★★ |
| 12 | OWASP ZAP (DAST) | `zap-report.html` | ★★★ |
| 13 | Pipeline GitLab (jobs verdes) | Build → Pipelines | ★★★ |
| 14 | Artefatos da pipeline | artifacts dos jobs | ★★ |
| 15 | Vulnerability report (GitLab) | Secure → Vulnerability report | ★★ |
| 16 | Cabeçalhos de segurança HTTP | DevTools → Network → Headers | ★★ |
| 17 | Proteção CSRF | POST sem token → HTTP 400 | ★ |
| 18 | Brute force / bloqueio | 5 logins errados → conta bloqueada | ★★ |
| 19 | Logs centrais / Fail2Ban | `logs/` ou `docker compose logs syslog` | ★ |

---

## 2. O que cada categoria de print comprova

| Conceito da disciplina | Prints que comprovam |
|---|---|
| **DevOps** | #1 containers, #8 testes automatizados, #13 pipeline |
| **DevSecOps** | #10 SAST, #11 SCA, #12 DAST, #15 vulnerability report |
| **Docker / Containerização** | #1 `docker ps`, #5 health, #14 imagem buildada |
| **SAST** | #10 Bandit sem severidade ALTA |
| **DAST** | #12 relatório do OWASP ZAP |
| **Monitoramento / Observabilidade** | #19 logs centrais (syslog-ng) e Fail2Ban |
| **Segurança (defesas)** | #16 headers, #17 CSRF, #18 brute force |
| **PostgreSQL** | #6 pgAdmin conectado, #7 registros nas tabelas |
| **Pipeline / CI/CD** | #13 jobs verdes, #14 artefatos, #15 report |
| **Testes / Qualidade** | #8 pytest + cobertura, #9 flake8 |

---

## 3. Prints obrigatórios, por área (com o que destacar)

### 3.1 Aplicação
- **Login** (#2): mostre a tela inicial em `localhost:8000`.
- **Dashboard** (#3): logado como `demo`, com tarefas visíveis.
- **CRUD** (#4): destaque uma tarefa sendo criada/editada/concluída.
- **CSRF** (#17): tente um POST sem token (ex.: via DevTools/curl) e mostre a
  rejeição **HTTP 400** — comprova proteção contra CSRF.
- **Brute force** (#18): erre a senha 5 vezes e capture a mensagem de **conta
  bloqueada** — comprova rate limiting + bloqueio temporário.
- **Health** (#5): `curl http://localhost:8000/health` retornando **200** com o
  banco "up".

### 3.2 Docker
- **`docker ps`** (#1): containers `taskguard-db`, `taskguard-web`,
  `taskguard-syslog` rodando (coluna STATUS = *Up/healthy*).
- **Compose funcionando**: a saída de `docker compose up` ou `docker compose ps`.
- **Logs** (#19): `docker compose logs web` mostrando a app inicializada.

### 3.3 PostgreSQL
- **pgAdmin conectado** (#6): árvore *Servers → TaskGuard → … → Tables* com as
  tabelas **`users`** e **`tasks`** visíveis. **Este é um dos prints mais fortes**
  para comprovar a troca de SQLite por PostgreSQL.
- **Registros** (#7): *View/Edit Data → All Rows* mostrando o usuário `demo` e as
  tarefas demo persistidas.

### 3.4 Pipeline (GitLab CI/CD)
- **Stages/Jobs verdes** (#13): **Build → Pipelines**, com os 6 estágios e os 7
  jobs concluídos (`lint`, `test`, `sast`, `dependency-check`, `docker-build`,
  `dast`, `deploy-stage`). **Print principal de DevOps/CI.**
- **Artefatos** (#14): a lista de artifacts (JUnit, cobertura, SARIF, relatórios,
  imagem `taskguard-ci.tar.gz`, relatório ZAP).
- **Security reports** (#15): **Secure → Vulnerability report** agregando SAST +
  dependências.

### 3.5 Segurança
- **Bandit / SAST** (#10): saída "No issues identified" (ou JSON sem severidade
  ALTA).
- **Dependency-Check / SCA** (#11): abertura do `dependency-check-report.html`.
- **OWASP ZAP / DAST** (#12): abertura do `zap-report.html` com o resumo de
  alertas.
- **Headers HTTP** (#16): DevTools do navegador → aba **Network** → clique na
  requisição → **Response Headers**, destacando `Content-Security-Policy`,
  `Strict-Transport-Security`, `X-Frame-Options`, `X-Content-Type-Options`.
- **Fail2Ban / logs** (#19): conteúdo de `logs/security.log` ou
  `docker compose logs syslog` evidenciando a detecção de eventos.

### 3.6 Testes
- **pytest + cobertura** (#8): `pytest --cov=app --cov-report=term-missing`
  mostrando **29 passed** e a cobertura (~86,65%). **Print principal de
  qualidade.**
- **flake8** (#9): execução sem nenhuma saída (código limpo).

---

## 4. Quais prints **mais impressionam** a banca

Em ordem de impacto acadêmico:

1. **Pipeline GitLab inteira verde** (#13) — prova automação ponta a ponta.
2. **Relatório do OWASP ZAP** (#12) — DAST é o que mais diferencia um trabalho
   "DevSecOps" de um "DevOps".
3. **Bandit limpo** (#10) + **Dependency-Check** (#11) — a tríade SAST/SCA/DAST
   completa.
4. **pgAdmin com as tabelas** (#6) — comprova persistência real em PostgreSQL.
5. **Cobertura de testes** (#8) — qualidade mensurável.
6. **Vulnerability report do GitLab** (#15) — integração nativa de segurança.

> Dica: se o tempo for curto, garanta **pelo menos** os prints #1, #6, #8, #10,
> #12 e #13. Eles cobrem Docker, PostgreSQL, Testes, SAST, DAST e Pipeline.

---

## 5. Mapeamento print → moldura do relatório

O `relatorio_academico.tex` tem **4 molduras** na seção *Evidências*. Sugestão de
preenchimento:

| Moldura no relatório | Print sugerido |
|---|---|
| **Figura 1 — Tela de login** | #2 |
| **Figura 2 — Painel de tarefas** | #3 |
| **Figura 3 — Relatório do OWASP ZAP (DAST)** | #12 |
| **Figura 4 — Pipeline no GitLab CI/CD** | #13 |

**Como inserir no LaTeX:** salve as imagens em `docs/screenshots/` e, em cada
moldura, substitua o conteúdo por:

```latex
\includegraphics[width=\linewidth]{screenshots/login.png}
```

Os prints restantes (#1, #6, #8, #10, #11, #15, #16, #18…) ficam ótimos em um
**apêndice de evidências** ao final do relatório.

---

## 6. Boas práticas de captura

- **Janela maximizada** e zoom adequado: texto pequeno demais prejudica a leitura
  na impressão.
- **Destaque** o que importa (retângulo/seta) — ex.: a coluna *healthy* no
  `docker ps`, o número de testes no pytest, o status verde dos jobs.
- **Anonimize**: borre senhas, tokens, `NVD_API_KEY` e e-mails reais.
- **Consistência**: use o mesmo tema/idioma do navegador em todos os prints.
- **Nomeie os arquivos** de forma clara: `01-docker-ps.png`, `06-pgadmin.png`,
  `13-pipeline.png`… facilita montar o relatório depois.

---

### Checklist final de evidências

```
APLICAÇÃO     [ ] login  [ ] dashboard  [ ] CRUD  [ ] CSRF 400  [ ] brute force  [ ] /health 200
DOCKER        [ ] docker ps  [ ] compose up  [ ] logs
POSTGRESQL    [ ] pgAdmin conectado  [ ] tabelas users/tasks  [ ] registros
PIPELINE      [ ] jobs verdes  [ ] artifacts  [ ] vulnerability report
SEGURANÇA     [ ] Bandit  [ ] Dependency-Check  [ ] OWASP ZAP  [ ] headers HTTP  [ ] logs/Fail2Ban
TESTES        [ ] pytest + cobertura  [ ] flake8
```
