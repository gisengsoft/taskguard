# Guia de Implementação Local — TaskGuard (Windows)

Guia passo a passo para rodar o **TaskGuard** do zero em um PC **Windows 10/11**,
incluindo Docker, PostgreSQL, pgAdmin, testes de segurança e publicação da
pipeline no **GitLab CI/CD**.

> Há **dois caminhos** de execução. Escolha um:
> - **Caminho A — Docker Compose** (recomendado): sobe banco + app + logs com um
>   comando. É o cenário que o projeto foi desenhado para usar.
> - **Caminho B — Local sem Docker**: roda o Flask direto no Windows usando um
>   PostgreSQL instalado na máquina. Útil para depurar o código.
>
> Você **não precisa** dos dois. Se tem Docker Desktop, vá pelo Caminho A.

---

## Sumário

1. [Pré-requisitos e o que instalar](#1-pré-requisitos-e-o-que-instalar)
2. [Obter o projeto](#2-obter-o-projeto)
3. [Configuração do arquivo `.env`](#3-configuração-do-arquivo-env)
4. [Caminho A — Executar com Docker Compose](#4-caminho-a--executar-com-docker-compose)
5. [Conectar o pgAdmin ao PostgreSQL](#5-conectar-o-pgadmin-ao-postgresql)
6. [Caminho B — Executar localmente sem Docker](#6-caminho-b--executar-localmente-sem-docker)
7. [Testes e qualidade (pytest, flake8, Bandit, Dependency-Check, ZAP)](#7-testes-e-qualidade)
8. [Publicar a pipeline no GitLab CI/CD](#8-publicar-a-pipeline-no-gitlab-cicd)
9. [Troubleshooting (problemas comuns no Windows)](#9-troubleshooting)
10. [Checklist rápido](#10-checklist-rápido)

---

## 1. Pré-requisitos e o que instalar

| Ferramenta | Para quê | Obrigatório? |
|---|---|---|
| **Docker Desktop** | Subir banco + app + logs (Caminho A) e rodar Dependency-Check / ZAP | Sim (Caminho A) |
| **Git** | Clonar/enviar o repositório ao GitLab + Git Bash p/ scripts `.sh` | Sim |
| **Python 3.12** | Rodar testes/flake8/Bandit e o Caminho B | Sim |
| **PostgreSQL 16 (local)** | Banco para o **Caminho B** (no Caminho A o banco roda em container) | Só no Caminho B |
| **pgAdmin 4** | Inspecionar o banco (tabelas, registros) e tirar prints | Recomendado |
| **GitLab Runner** | Executar a pipeline na **sua** máquina | **Não** — veja a seção 8 |

### 1.1 Docker Desktop

1. Baixe em <https://www.docker.com/products/docker-desktop/> e instale.
2. Durante a instalação, mantenha marcada a opção **WSL 2** (recomendado).
3. Reinicie o Windows se solicitado.
4. Abra o **Docker Desktop** e aguarde o status ficar **"Engine running"**.
5. Confirme no **PowerShell**:
   ```powershell
   docker --version
   docker compose version
   ```
   > Se aparecer "Cannot connect to the Docker daemon", o Docker Desktop **não
   > está aberto/rodando**. Abra-o antes de qualquer comando `docker`.

### 1.2 Git

1. Baixe em <https://git-scm.com/download/win> e instale (aceite os padrões).
2. Isso também instala o **Git Bash**, necessário para rodar os scripts `.sh`
   (`run_sast.sh`, `run_dependency_check.sh`, `run_dast.sh`) no Windows.
3. Confirme:
   ```powershell
   git --version
   ```

### 1.3 Python 3.12

1. Baixe em <https://www.python.org/downloads/> (versão **3.12.x**).
2. **MUITO IMPORTANTE:** na primeira tela do instalador, marque
   **"Add python.exe to PATH"**.
3. Confirme:
   ```powershell
   python --version
   pip --version
   ```

### 1.4 PostgreSQL 16 local — **somente para o Caminho B**

> No **Caminho A (Docker)** o PostgreSQL já roda dentro de um container; você
> **não** precisa instalar o Postgres na máquina. Pule esta etapa se for usar
> Docker.

1. Baixe o instalador em <https://www.postgresql.org/download/windows/>
   (EnterpriseDB), versão **16**.
2. Durante a instalação:
   - Defina a senha do superusuário `postgres` (anote-a).
   - Mantenha a porta padrão **5432**.
   - O instalador já inclui o **pgAdmin 4** (pode marcar para instalar junto).
3. Após instalar, crie o banco/usuário do projeto (veja a seção 6.2).

### 1.5 pgAdmin 4

- Vem junto com o instalador do PostgreSQL. Se preferir separado, baixe em
  <https://www.pgadmin.org/download/>.
- Serve para você **ver as tabelas e registros** e tirar os prints de evidência.
  Funciona tanto com o Postgres do Docker (Caminho A) quanto com o local
  (Caminho B), pois ambos expõem a porta **5432** em `localhost`.

---

## 2. Obter o projeto

1. Extraia o `taskguard.zip` em uma pasta sem espaços/acentos no caminho, por
   exemplo `C:\dev\taskguard`.
2. Abra o **PowerShell** nessa pasta (Shift + clique direito → *Abrir janela do
   PowerShell aqui*) ou:
   ```powershell
   cd C:\dev\taskguard
   ```
3. Confira se os arquivos-chave estão presentes:
   ```powershell
   dir
   ```
   Você deve ver `docker-compose.yml`, `Dockerfile`, `.gitlab-ci.yml`,
   `requirements.txt`, as pastas `app\`, `scripts\`, `docs\`, etc.

---

## 3. Configuração do arquivo `.env`

A aplicação lê as configurações de um arquivo **`.env`** (que **não** vai para o
Git). Há um modelo pronto em **`.env.example`**.

1. Copie o modelo:
   ```powershell
   copy .env.example .env
   ```
2. Gere uma **SECRET_KEY** forte e copie o valor exibido:
   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
3. Abra o `.env` (Bloco de Notas, VS Code…) e ajuste:

   ```dotenv
   # Ambiente
   FLASK_CONFIG=development          # production quando rodar via Docker/Compose

   # Cole aqui a chave gerada no passo 2
   SECRET_KEY=<cole-a-chave-de-64-hex-aqui>

   # Credenciais do PostgreSQL (valores padrão do projeto)
   POSTGRES_USER=taskguard
   POSTGRES_PASSWORD=taskguard        # TROQUE antes de publicar
   POSTGRES_DB=taskguard

   # URL de conexão da aplicação:
   #  - Caminho A (Docker Compose): host = nome do serviço 'db'
   DATABASE_URL=postgresql+psycopg://taskguard:taskguard@db:5432/taskguard
   #  - Caminho B (local, sem Docker): troque 'db' por 'localhost'
   #    DATABASE_URL=postgresql+psycopg://taskguard:taskguard@localhost:5432/taskguard
   ```

   > **Resumo da diferença de host:**
   > - Dentro do Docker Compose, a app fala com o banco pelo nome de serviço
   >   **`db`** (`...@db:5432/...`).
   > - Rodando o Flask direto no Windows, use **`localhost`**
   >   (`...@localhost:5432/...`).

4. **Portas usadas pelo projeto** (deixe livres ou ajuste no `.env`/compose):

   | Porta | Serviço | Onde |
   |---|---|---|
   | **8000** | App Flask (Gunicorn) | container `web` (Caminho A) |
   | **5000** | App Flask (dev server) | execução local (Caminho B) |
   | **5432** | PostgreSQL | container `db` ou Postgres local |
   | **5514/udp** | syslog-ng (logs centrais) | container `syslog` |

---

## 4. Caminho A — Executar com Docker Compose

Cenário recomendado. Sobe **PostgreSQL + aplicação + coletor de logs** juntos.

> Garanta que o **Docker Desktop esteja aberto** ("Engine running").

### 4.1 Build e subida dos containers

```powershell
docker compose up -d --build
```

- `--build` constrói a imagem da aplicação a partir do `Dockerfile`.
- `-d` roda em segundo plano.
- A app **só inicia depois** que o PostgreSQL responder ao *healthcheck*
  (`pg_isready`) — isso é automático via `depends_on`.

### 4.2 Conferir os containers de pé

```powershell
docker compose ps
docker ps
```

Você deve ver `taskguard-db`, `taskguard-web` e `taskguard-syslog` rodando.

### 4.3 Inicializar o banco (criar tabelas + dados demo)

As tabelas são criadas automaticamente quando a app sobe. Para popular com um
**usuário e tarefas de demonstração**:

```powershell
docker compose exec web python scripts/init_db.py --seed
```

> Credenciais demo (apenas para desenvolvimento): **usuário** `demo` /
> **senha** `Demo@1234`.

### 4.4 Acessar a aplicação

Abra no navegador: <http://localhost:8000>

### 4.5 Health check

```powershell
curl http://localhost:8000/health
```

Resposta esperada: HTTP **200** com um JSON indicando `status: healthy` e o
banco como disponível. (Se o banco estiver fora, retorna **503**.)

### 4.6 Ver logs

```powershell
docker compose logs -f web      # logs da aplicação (Ctrl+C para sair)
docker compose logs db          # logs do PostgreSQL
docker compose logs syslog      # coletor central de logs
```

### 4.7 Parar / reiniciar

```powershell
docker compose stop             # para sem apagar nada
docker compose start            # sobe de novo
docker compose down             # remove containers (mantém o volume do banco)
docker compose down -v          # remove containers E o volume (apaga o banco!)
```

> O banco persiste no volume nomeado **`taskguard-db-data`**. Um `down` comum
> **não** apaga os dados; só o `down -v` apaga.

---

## 5. Conectar o pgAdmin ao PostgreSQL

Funciona com o banco do **Docker** (Caminho A) ou o **local** (Caminho B) —
ambos expõem a porta **5432** em `localhost`.

1. Abra o **pgAdmin 4**.
2. No painel esquerdo, clique com o direito em **Servers → Register → Server…**
3. Aba **General**: em *Name*, digite `TaskGuard`.
4. Aba **Connection**, preencha:

   | Campo | Valor |
   |---|---|
   | **Host name/address** | `localhost` |
   | **Port** | `5432` |
   | **Maintenance database** | `taskguard` |
   | **Username** | `taskguard` |
   | **Password** | `taskguard` (ou o que você definiu no `.env`) |

   Marque **Save password** se quiser.
5. Clique em **Save**. O servidor aparece conectado.
6. Para ver as tabelas:
   **Servers → TaskGuard → Databases → taskguard → Schemas → public → Tables**.
   Você verá as tabelas **`users`** e **`tasks`**.
7. Para ver registros: clique com o direito em uma tabela →
   **View/Edit Data → All Rows**.

> **Importante:** se você usar o **Caminho A (Docker)**, o pgAdmin conecta em
> `localhost:5432` porque o `docker-compose.yml` **publica** essa porta no host
> (`ports: "5432:5432"`). Se a porta 5432 já estiver ocupada por um Postgres
> instalado na máquina, veja a seção 9.

---

## 6. Caminho B — Executar localmente sem Docker

Use este caminho para depurar o Flask diretamente. Requer **PostgreSQL 16
instalado** no Windows (seção 1.4).

### 6.1 Criar e ativar o ambiente virtual

```powershell
cd C:\dev\taskguard
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> Se o PowerShell bloquear o script de ativação ("execution policy"), rode uma
> vez:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```
> e ative novamente. (Alternativa: use `.\.venv\Scripts\activate.bat` no CMD.)

Instale as dependências:

```powershell
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 6.2 Criar o banco e o usuário no PostgreSQL local

Abra o **SQL Shell (psql)** (vem com o Postgres) e entre como `postgres`. Depois
execute:

```sql
CREATE USER taskguard WITH PASSWORD 'taskguard';
CREATE DATABASE taskguard OWNER taskguard;
GRANT ALL PRIVILEGES ON DATABASE taskguard TO taskguard;
```

### 6.3 Apontar o `.env` para `localhost`

No `.env`, garanta:

```dotenv
FLASK_CONFIG=development
DATABASE_URL=postgresql+psycopg://taskguard:taskguard@localhost:5432/taskguard
```

### 6.4 Criar as tabelas e dados demo

```powershell
python scripts/init_db.py --seed
```

### 6.5 Rodar a aplicação

```powershell
python run.py
```

Acesse <http://localhost:5000> (no Caminho B o servidor de desenvolvimento usa a
porta **5000**, definida por `FLASK_PORT`).

---

## 7. Testes e qualidade

> Ative o ambiente virtual antes (`.\.venv\Scripts\Activate.ps1`) para os
> comandos Python. Para os scripts **`.sh`**, use o **Git Bash** (clique direito
> na pasta → *Git Bash Here*). Abaixo dou **as duas formas**: o script `.sh` e o
> comando direto equivalente em PowerShell.

### 7.1 Testes automatizados (pytest)

```powershell
pytest
```

Para ver a cobertura:

```powershell
pytest --cov=app --cov-report=term-missing
```

> Resultado esperado do projeto: **29 testes aprovados**, cobertura **~86,65%**
> (acima do mínimo de 80% exigido pela pipeline).

### 7.2 Estilo de código (flake8)

```powershell
flake8 app run.py config.py scripts/init_db.py
```

Sem saída = nenhum problema de estilo.

### 7.3 SAST — Bandit (análise estática)

**Git Bash:**
```bash
bash scripts/run_sast.sh
```

**PowerShell (direto):**
```powershell
bandit -r app run.py config.py -c pyproject.toml -f screen
```

> Resultado esperado: **nenhuma** vulnerabilidade de severidade ALTA. O relatório
> JSON é salvo em `reports/bandit-report.json`.

### 7.4 SCA — OWASP Dependency-Check (dependências vulneráveis)

Roda em **container Docker** (não precisa de Java instalado). Exige **Docker
Desktop aberto**.

**Git Bash:**
```bash
bash scripts/run_dependency_check.sh
```

**PowerShell (direto):**
```powershell
mkdir reports -Force ; mkdir $HOME\.dependency-check-data -Force
docker run --rm `
  -v "${PWD}:/src:ro" `
  -v "${PWD}\reports:/report:rw" `
  -v "$HOME\.dependency-check-data:/usr/share/dependency-check/data:rw" `
  owasp/dependency-check:latest `
  --scan /src --project TaskGuard `
  --format HTML --format JSON `
  --out /report --failOnCVSS 7 --enableExperimental
```

> A **primeira execução baixa a base de CVEs da NVD e pode demorar bastante**.
> Para acelerar muito, gere uma chave gratuita em
> <https://nvd.nist.gov/developers/request-an-api-key> e exporte
> `NVD_API_KEY` antes de rodar (no Git Bash: `export NVD_API_KEY=xxxx`). A flag
> `--failOnCVSS 7` faz falhar se houver CVE com CVSS ≥ 7. O relatório fica em
> `reports/dependency-check-report.html`.

### 7.5 DAST — OWASP ZAP (teste dinâmico)

Sobe a app em container e faz uma varredura passiva (ZAP Baseline). Exige
**Docker Desktop aberto**.

**Forma simples (PowerShell), com a app já no ar via Compose:**
```powershell
docker compose up -d --build web
docker compose --profile security run --rm zap
```

**Ou pelo script (Git Bash), que sobe e derruba tudo sozinho:**
```bash
bash scripts/run_dast.sh
```

> O relatório é gerado em `pipeline/zap/zap-report.html` (o script também copia
> para `reports/`). Abra-o no navegador para ver os alertas.

---

## 8. Publicar a pipeline no GitLab CI/CD

A pipeline está definida em **`.gitlab-ci.yml`** com **6 estágios** e **7 jobs**:
`lint` → `test` → (`sast` + `dependency-check` em paralelo no estágio
`security`) → `docker-build` → `dast` → `deploy-stage`.

### 8.1 Criar o repositório no GitLab

1. Crie a conta em <https://gitlab.com> (se ainda não tiver).
2. **New project → Create blank project**. Dê o nome `taskguard` e crie.
3. **Importante:** não inicialize com README (você já tem um).

### 8.2 Enviar o código (push)

Na pasta do projeto (PowerShell ou Git Bash):

```bash
git init
git add .
git commit -m "TaskGuard: projeto DevSecOps com pipeline GitLab CI/CD"
git branch -M main
git remote add origin https://gitlab.com/<SEU-USUARIO>/taskguard.git
git push -u origin main
```

> Troque `<SEU-USUARIO>` pelo seu usuário do GitLab. O `git push` já dispara a
> pipeline automaticamente.

### 8.3 Configurar variáveis/secrets (opcional, mas recomendado)

No projeto do GitLab: **Settings → CI/CD → Variables → Add variable**.

| Variável | Valor | Para quê |
|---|---|---|
| `NVD_API_KEY` | sua chave da NVD | Acelera o job `dependency-check` |
| `SECRET_KEY` | uma chave forte | Caso queira usá-la em jobs de deploy |

Marque **Masked** (e **Protected** se aplicável) para valores sensíveis.

### 8.4 Acompanhar a execução

- **Build → Pipelines**: veja os estágios e jobs (verdes = passou).
- Clique em um job para ver o log completo.
- **Build → Artifacts** (ou dentro de cada job): baixe os artefatos —
  `reports/junit.xml`, cobertura, `bandit.sarif`, relatório do Dependency-Check,
  a imagem `taskguard-ci.tar.gz` e o relatório do ZAP.
- **Secure → Vulnerability report**: o GitLab agrega os achados de SAST e de
  dependências (campos `reports:sast` e `reports:dependency_scanning`).

### 8.5 Sobre o **GitLab Runner** (você precisa instalar?)

- **Não, na maioria dos casos.** O **GitLab.com** já oferece *shared runners*
  gratuitos que executam toda a pipeline — basta dar `push`.
- Os jobs `docker-build` e `dast` usam **Docker-in-Docker (DinD)**, que exige um
  runner com modo **privileged**. Os shared runners do GitLab.com **suportam**
  isso por padrão.
- Você só precisaria instalar um **GitLab Runner próprio** se quisesse rodar a
  pipeline na **sua** máquina/servidor (ex.: GitLab self-hosted) — aí seria
  preciso registrar o runner e habilitar `privileged = true` na config dele.

---

## 9. Troubleshooting

**"Cannot connect to the Docker daemon" / `docker` não responde**
O Docker Desktop não está aberto. Abra-o e espere "Engine running".

**Porta 5432 já está em uso**
Você tem um PostgreSQL local ocupando a 5432 e tentou subir o container na mesma
porta. Opções: (a) pare o serviço Postgres do Windows enquanto usa o Docker; ou
(b) no `docker-compose.yml`, mude o mapeamento do `db` para `"5433:5432"` e, no
pgAdmin, conecte em `localhost:5433`.

**Porta 8000 já em uso**
Outro processo está usando a 8000. Descubra com
`netstat -ano | findstr :8000` e encerre o processo, ou mude o mapeamento da
porta do serviço `web` no compose.

**Scripts `.sh` falham com "bad interpreter" / `\r` no Git Bash**
Os arquivos foram salvos com quebras de linha do Windows (CRLF). Converta para
LF (no VS Code, canto inferior direito: troque **CRLF → LF** e salve) ou
configure `git config --global core.autocrlf input` antes de clonar.

**`Activate.ps1` bloqueado pela política de execução**
Rode `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` e
ative de novo, ou use o CMD com `.\.venv\Scripts\activate.bat`.

**App retorna 503 no `/health`**
O banco não está acessível. No Caminho A, confirme `taskguard-db` rodando
(`docker compose ps`). No Caminho B, confirme o serviço PostgreSQL do Windows
ativo e o `DATABASE_URL` apontando para `localhost`.

**`psql`/conexão recusada no Caminho B**
Verifique se o serviço **postgresql-x64-16** está em execução em
*Serviços* do Windows, e se o usuário/senha/банco do passo 6.2 batem com o `.env`.

**Primeira execução do Dependency-Check muito lenta**
É o download da base da NVD. Configure a `NVD_API_KEY` (seção 7.4) e reaproveite
o cache em `~/.dependency-check-data` nas próximas execuções.

---

## 10. Checklist rápido

```
[ ] Docker Desktop instalado e aberto ("Engine running")
[ ] Git e Python 3.12 instalados (no PATH)
[ ] taskguard.zip extraído em C:\dev\taskguard
[ ] .env criado a partir do .env.example
[ ] SECRET_KEY forte gerada e colada no .env
[ ] (Caminho A) docker compose up -d --build  → containers de pé
[ ] docker compose exec web python scripts/init_db.py --seed
[ ] http://localhost:8000 abre e o login com demo / Demo@1234 funciona
[ ] curl http://localhost:8000/health  → 200
[ ] pgAdmin conectado em localhost:5432 (db/usuário taskguard) e tabelas visíveis
[ ] pytest  → 29 passam (cobertura ~86,65%)
[ ] flake8  → sem erros
[ ] Bandit (SAST)  → sem severidade ALTA
[ ] Dependency-Check (SCA)  → sem CVSS ≥ 7
[ ] OWASP ZAP (DAST)  → relatório gerado
[ ] Repositório criado no GitLab e git push feito
[ ] Pipeline verde em Build → Pipelines
```

---

### Credenciais e portas de referência

| Item | Valor padrão |
|---|---|
| Usuário demo (app) | `demo` / `Demo@1234` |
| PostgreSQL (usuário/senha/banco) | `taskguard` / `taskguard` / `taskguard` |
| App via Docker | <http://localhost:8000> |
| App local (Caminho B) | <http://localhost:5000> |
| PostgreSQL / pgAdmin | `localhost:5432` |

> **Antes de publicar:** troque `SECRET_KEY` e `POSTGRES_PASSWORD`, e nunca
> versione o arquivo `.env` real. As credenciais demo servem apenas para
> desenvolvimento/avaliação.
