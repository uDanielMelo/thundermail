# ⚡ ThunderMail

Plataforma de e-mail marketing e ferramentas de negócio para pequenas empresas.

---

## Sobre o projeto

ThunderMail é uma plataforma SaaS multi-tenant construída com Django, que permite às empresas gerenciar contatos, disparar campanhas de e-mail e SMS, assinar contratos digitais e, em breve, emitir cobranças — tudo em um único lugar.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python · Django 6.0.3 |
| Fila de tarefas | Celery 5.6.2 + Redis 7 |
| Banco de dados | PostgreSQL 16 |
| Envio de e-mail | Resend |
| Envio de SMS | Twilio |
| Containerização | Docker + Docker Compose |

---

## Módulos

### ThunderMail (core)
- **Contacts** — cadastro de contatos, importação via CSV (e-mail + telefone), agrupamento
- **Campaigns** — criação e disparo de campanhas de e-mail e SMS
- **Mailer** — serviço de envio assíncrono via Celery + Resend

### ThunderTools
Menu de ferramentas de negócio dentro da plataforma.

- **Contracts** — assinatura digital de contratos *(disponível)*
- **Cobranças** — geração de cobranças via Asaas (Pix, boleto, cartão) *(em desenvolvimento)*
- **Tasks** — gerenciamento de tarefas e projetos com Kanban *(em desenvolvimento)*

### Accounts & Auth
- Cadastro e login por organização (multi-tenant)
- Recuperação de senha por e-mail com link de expiração em 1h
- Gerenciamento de integrações (Resend, Twilio, Asaas) por organização

---

## Como rodar localmente

### Pré-requisitos
- Docker Desktop instalado e rodando
- Arquivo `.env.docker` configurado (veja `.env.docker` de exemplo no repositório)

### Subindo com Docker Compose

```bash
docker compose up
```

A aplicação estará disponível em `http://localhost:8000`.

O Compose sobe automaticamente:
- `db` — PostgreSQL 16 (com healthcheck)
- `redis` — Redis 7
- `web` — Django + migrações automáticas
- `celery` — worker para tarefas assíncronas

### Rodando sem Docker

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.docker .env
# edite o .env com suas credenciais

# Rodar migrações
python manage.py migrate

# Iniciar servidor
python manage.py runserver
```

---

## Variáveis de ambiente

Crie um arquivo `.env` (ou use `.env.docker` para Docker) com as seguintes variáveis:

```env
SECRET_KEY=sua-secret-key
DEBUG=True

# Banco de dados
DATABASE_URL=postgres://postgres:postgres@db:5432/thundermail_new

# Redis
REDIS_URL=redis://redis:6379/0

# Resend (envio de e-mail)
RESEND_API_KEY=re_...

# Twilio (envio de SMS)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
```

---

## Estrutura do projeto

```
thundermail/
├── apps/
│   ├── accounts/       # Autenticação e organizações
│   ├── campaigns/      # Campanhas de e-mail e SMS
│   ├── contacts/       # Contatos e grupos
│   ├── contracts/      # Assinatura de contratos (ThunderTools)
│   ├── integrations/   # Configurações de integrações
│   └── mailer/         # Serviço de envio de e-mail
├── core/               # Settings, URLs e configuração Django
├── static/             # Arquivos estáticos
├── templates/          # Templates HTML
├── docker-compose.yml
├── Dockerfile
├── manage.py
└── requirements.txt
```

---

## Roadmap

- [x] Campanhas de e-mail
- [x] Campanhas de SMS (Twilio)
- [x] Importação de contatos via CSV
- [x] Assinatura digital de contratos
- [x] Recuperação de senha por e-mail
- [ ] ThunderTools Cobranças — Asaas (Pix, boleto, cartão)
- [ ] ThunderTasks — Kanban e gerenciamento de projetos
- [ ] Credenciais de integração por organização (multi-tenant)
- [ ] Dashboard financeiro

---

## Licença

MIT