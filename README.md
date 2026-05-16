# ThunderMail

**Plataforma SaaS de e-mail marketing e automação para pequenas empresas**

> Django · PostgreSQL · Celery · Redis · Resend · Asaas · Docker · Railway

**Produção:** [https://thundermail.com.br](https://thundermail.com.br)

---

## Projeto de Extensão — USCS

Este projeto foi desenvolvido como **Projeto de Extensão** do curso de **Análise e Desenvolvimento de Sistemas** da [USCS — Universidade Municipal de São Caetano do Sul](https://www.uscs.edu.br/).

A proposta de extensão consiste em aplicar os conhecimentos adquiridos ao longo do curso na construção de um produto de software real, com deploy em produção, voltado ao mercado de pequenas empresas brasileiras. O projeto cobre disciplinas como Engenharia de Software, Banco de Dados, Programação Web, Arquitetura de Sistemas e Infraestrutura em Nuvem.

| | |
|---|---|
| **Instituição** | USCS — Universidade Municipal de São Caetano do Sul |
| **Curso** | Análise e Desenvolvimento de Sistemas |
| **Modalidade** | Projeto de Extensão |
| **Aluno** | Daniel Melo |

---

## Visão Geral

ThunderMail é uma plataforma **multi-tenant** construída em Django que centraliza comunicação por e-mail, gestão de contatos, cobranças e gerenciamento de projetos em um único produto — o **ThunderTools**.

Cada cliente é isolado dentro de uma **Organização**. Todos os dados, campanhas, contatos e configurações são sempre escopados à organização, garantindo separação total entre clientes diferentes na mesma instalação.

---

## Arquitetura

### Visão de alto nível

```
Usuário (browser)
       │
       ▼
  Django (Gunicorn)          ←──── Railway (web process)
       │
       ├── PostgreSQL         ←──── banco relacional, todos os dados
       ├── Redis              ←──── broker de mensagens do Celery
       │
       ├── Resend             ←──── envio de e-mails transacionais e campanhas
       └── Asaas              ←──── geração de cobranças (Pix, Boleto, Cartão)

Celery Worker                ←──── Railway (worker process)
       │
       └── processa tarefas assíncronas: envio de campanhas em lote,
           notificações, lembretes

Celery Beat                  ←──── Railway (beat process)
       │
       └── agendamento: dispara campanhas agendadas a cada 60s,
           lembretes diários às 8h
```

### Multi-tenancy

O modelo central é a `Organization`. Todo recurso do sistema (campanha, contato, cobrança, tarefa) possui uma FK para `Organization`, e nenhuma view retorna dados fora da organização do usuário autenticado.

- `OrganizationMember` — vincula usuário a uma organização com papel (`admin` / `member`)
- `MemberPermission` — permissões granulares por módulo (campanhas, contatos, billing, etc.)
- `get_user_organization(user)` — helper em `apps/accounts/middleware.py` que resolve a org ativa
- `@require_permission(module)` — decorator em `apps/accounts/decorators.py` que bloqueia views sem permissão

### Envio de campanhas (Celery)

O envio em massa usa um pipeline de tarefas Celery para não bloquear o servidor web:

```
Celery Beat (60s)
  └── send_scheduled_campaigns()
        └── para cada campanha agendada:
              └── send_campaign_in_batches(campaign_id, offset, batch_size=30)
                    ├── envia lote de 30 e-mails via Resend
                    ├── usa F() expressions para atualizar contadores sem race condition
                    ├── agenda próximo lote com delay de 5s
                    └── registra resultados em CampaignLog
```

Campanhas presas em estado "enviando" por mais de 30 minutos são recuperadas automaticamente.

### Billing / Asaas

O módulo de cobranças integra com a API REST do Asaas:

```
apps/billing/services/asaas.py
  └── AsaasClient
        ├── create_charge()    → Pix, Boleto ou Cartão
        ├── get_charge()       → consulta status
        └── delete_charge()    → cancelamento

Webhook: POST /billing/webhook/
  └── validado pelo header ASAAS_WEBHOOK_TOKEN
  └── atualiza status da cobrança no banco
```

Resolução da API key: `organization.asaas_api_key` → `settings.ASAAS_API_KEY` (env var).

---

## Stack Técnica

| Camada | Tecnologia |
|--------|-----------|
| Backend | Django 5 |
| Banco de dados | PostgreSQL (psycopg3) |
| Fila de tarefas | Celery 5 + Redis |
| Agendamento | Celery Beat |
| E-mail transacional | Resend |
| Pagamentos | Asaas (Pix, Boleto, Cartão) |
| Frontend | Django Templates + Tailwind CSS |
| Deploy | Railway |
| Containers | Docker + docker-compose |

---

## Estrutura do Projeto

```
thundermail/
├── apps/
│   ├── accounts/          # Autenticação, organizações, membros, permissões
│   ├── campaigns/         # Campanhas de e-mail
│   ├── contacts/          # Contatos, grupos, importação CSV
│   ├── mailer/            # Backend Resend + serviço send_campaign_email
│   ├── analytics/         # Logs e métricas de campanhas
│   ├── billing/           # Cobranças via Asaas + webhook
│   ├── tasks/             # Gerenciamento de projetos (Kanban)
│   ├── integrations/      # Configurações de integrações por organização
│   ├── contracts/         # Gestão de contratos
│   └── documents/         # Gestão de documentos
├── core/
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
├── templates/
├── static/
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── Procfile               # Processos Railway: web, worker, beat
└── entrypoint.sh          # Roda migrate antes de subir o gunicorn
```

---

## Módulos

### `accounts` — Autenticação e Organizações

- Registro, login e recuperação de senha
- Model `User` com `email` como `USERNAME_FIELD`
- Multi-tenant: cada usuário pertence a uma **Organização**
- Gerenciamento de membros com **permissões por módulo**
- Middleware `get_user_organization` e decorator `@require_permission`

### `contacts` — Gestão de Contatos

- Criação e edição de contatos individuais
- **Grupos de contatos** com relação M2M
- **Importação via CSV** — colunas: `email`, `nome`, `telefone`
- Validação e descarte de e-mails inválidos na importação

### `campaigns` — Campanhas de E-mail

- Criação de campanhas com seleção de grupo de contatos
- Envio em **lotes via Celery** (30 e-mails por lote, delay de 5s entre lotes)
- **Templates** de e-mail reutilizáveis
- **Agendamento** de campanhas com calendário visual
- Recuperação automática de campanhas travadas

### `mailer` — Backend de E-mail

- `ResendEmailBackend`: backend Django que envia via API Resend (não SMTP direto)
- `send_campaign_email()`: ponto único de envio usado por campanhas e notificações de billing
- Domínio de envio fixo: `thundermail.com.br`; cliente configura apenas o nome do remetente

### `analytics` — Métricas

- `CampaignLog`: registro de cada e-mail enviado (status, timestamps, erros)
- Painel de métricas por campanha e por organização

### `billing` — Cobranças

- Criação de cobranças via **API Asaas** (Pix, Boleto, Cartão de crédito)
- Exibição de QR Code Pix e linha digitável do boleto
- Envio de link de pagamento por e-mail
- **Webhook** para atualização automática de status (`/billing/webhook/`)

### `tasks` — Gerenciamento de Projetos

- Criação de **projetos** e **tarefas** por organização
- **Kanban** com drag-and-drop (A Fazer / Em Andamento / Concluído)
- Tarefas com título, descrição, prioridade, data de entrega e responsável
- **Comentários** por tarefa
- **Notificação por e-mail** ao atribuir tarefa
- **Celery Beat**: lembrete diário às 8h para tarefas com vencimento no dia

---

## Setup Local

### Pré-requisitos

- Python 3.11+
- PostgreSQL
- Redis
- Docker Desktop (opcional)

### 1. Clonar e criar ambiente virtual

```bash
git clone https://github.com/uDanielMelo/thundermail.git
cd thundermail
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz:

```env
SECRET_KEY=sua_secret_key_aqui
DEBUG=True
DATABASE_URL=postgres://usuario:senha@localhost:5432/thundermail
REDIS_URL=redis://localhost:6379/0

RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxx

ASAAS_API_KEY=$aact_xxxxxxxxxxxxxxxxxxxx
ASAAS_BASE_URL=https://sandbox.asaas.com/api/v3
ASAAS_WEBHOOK_TOKEN=seu_token_aqui

SITE_URL=http://localhost:8000
```

> **Nunca commite o `.env`** — ele está no `.gitignore`.

### 3. Migrations e superusuário

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Rodar o servidor

```bash
python manage.py runserver
```

### 5. Rodar Celery (em outros terminais)

```bash
# Worker
celery -A core worker --loglevel=info --pool=solo

# Beat (agendamentos)
celery -A core beat --loglevel=info
```

### 6. Via Docker

```bash
docker compose up --build
```

---

## Deploy (Railway)

O projeto está em produção no Railway conectado ao branch `main`. O arquivo `Procfile` define os três processos:

```
web:    gunicorn core.wsgi (via entrypoint.sh que roda migrate antes)
worker: celery -A core worker
beat:   celery -A core beat
```

```bash
# Trabalhe em uma branch de feature
git checkout -b feat/minha-feature
git add .
git commit -m "feat: nova funcionalidade"
git push origin feat/minha-feature

# Quando pronto para produção:
git checkout main
git merge feat/minha-feature
git push origin main   # Railway faz deploy automático
```

**Variáveis de ambiente necessárias no Railway:**

```
SECRET_KEY=...
DATABASE_URL=...
REDIS_URL=...
RESEND_API_KEY=...
ASAAS_API_KEY=...
ASAAS_WEBHOOK_TOKEN=...
ALLOWED_HOSTS=thundermail.com.br,thundermail-production.up.railway.app
CSRF_TRUSTED_ORIGINS=https://thundermail.com.br,https://thundermail-production.up.railway.app
SITE_URL=https://thundermail.com.br
```

---

## Segurança

- Todas as chaves de API ficam em variáveis de ambiente (`.env` / Railway Variables)
- O arquivo `.env` está no `.gitignore`
- Webhook do Asaas validado via header `ASAAS_WEBHOOK_TOKEN`
- Em caso de vazamento de chave, revogue imediatamente no painel do provedor

---

## Licença

MIT — veja [LICENSE](LICENSE) para detalhes.
