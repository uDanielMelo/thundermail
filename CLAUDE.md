# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Run locally
```bash
python manage.py migrate
python manage.py runserver

# Celery worker (separate terminal)
celery -A core worker --loglevel=info --pool=solo

# Celery beat scheduler (separate terminal)
celery -A core beat --loglevel=info
```

### Docker
```bash
docker compose up --build
```

### Django utilities
```bash
python manage.py makemigrations
python manage.py createsuperuser
python manage.py collectstatic
```

## Architecture

**ThunderMail** is a multi-tenant SaaS for email marketing targeting small businesses in Brazil. Stack: Django 5 + PostgreSQL + Celery + Redis + Resend + Asaas + Railway.

### Multi-tenancy
Every resource is scoped to an `Organization`. Users belong to orgs via `OrganizationMember` with roles (`admin`, `member`) and granular per-module permissions via `MemberPermission`. The helper `get_user_organization(user)` in `apps/accounts/middleware.py` retrieves the active org for a request. The decorator `@require_permission(module)` in `apps/accounts/decorators.py` gates views by role + module permission.

### Apps

| App | Responsibility |
|-----|---------------|
| `accounts` | Custom User (email as USERNAME_FIELD), Organizations, membership, permissions |
| `campaigns` | Campaign creation, scheduling, batch sending via Celery |
| `contacts` | Contact list, groups, CSV import |
| `mailer` | Resend API email backend (`ResendEmailBackend`) and `send_campaign_email` service |
| `analytics` | Campaign send logs and metrics |
| `billing` | Manual invoice generation via Asaas (PIX, Boleto, Credit Card) + webhook receiver |
| `tasks` | Kanban-style project/task management |
| `integrations` | Third-party integration settings (e.g. Asaas API key per org) |
| `contracts` | Contract management |
| `documents` | Document storage |

### Email sending
All outbound email goes through Resend (never direct SMTP). `apps/mailer/services.py` → `send_campaign_email()` is the single send entrypoint used by both campaigns and billing notifications. The domain is always `thundermail.com.br`; clients configure only the sender name.

### Campaign batch sending (Celery)
`send_scheduled_campaigns` runs every 60 s and dispatches `send_campaign_in_batches(campaign_id, offset, batch_size=30)` — batches of 30 with 5 s delays. Uses `F()` expressions to avoid race conditions on counters. Campaigns stuck in "enviando" for 30+ min are auto-recovered. Results land in `CampaignLog`.

### Billing / Asaas
`apps/billing/services/asaas.py` wraps the Asaas REST API. API key resolution order: `organization.asaas_api_key` → `settings.ASAAS_API_KEY` env var. Status updates arrive via webhook at `/billing/webhook/` (csrf_exempt, validated by `ASAAS_WEBHOOK_TOKEN` header). Default base URL is the Asaas **sandbox** (`ASAAS_BASE_URL` env var overrides).

### Key environment variables
`SECRET_KEY`, `DEBUG`, `DATABASE_URL`, `REDIS_URL`, `RESEND_API_KEY`, `ASAAS_API_KEY`, `ASAAS_BASE_URL`, `ASAAS_WEBHOOK_TOKEN`

### Deployment
Railway auto-deploys from `main`. Processes defined in `Procfile`: `web` (gunicorn), `worker` (celery worker), `beat` (celery beat). Migrations run automatically via `entrypoint.sh` before gunicorn starts.
