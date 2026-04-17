# ThunderMail

**Plataforma SaaS de e-mail marketing e automação para pequenas empresas**

> Django 6 · PostgreSQL · Celery · Redis · Resend · Twilio · Asaas · Docker · Railway

**Produção:** [https://thundermail.com.br](https://thundermail.com.br)

---

## Visão Geral

ThunderMail é uma plataforma multi-tenant construída em Django que centraliza comunicação por e-mail, SMS, gestão de contatos, cobranças e gerenciamento de projetos em um único produto — o **ThunderTools**.

---

## Stack Técnica

| Camada | Tecnologia |
|--------|-----------|
| Backend | Django 6.0.3 |
| Banco de dados | PostgreSQL (psycopg3) |
| Fila de tarefas | Celery 5.6 + Redis |
| Agendamento | Celery Beat |
| E-mail transacional | Resend (SMTP) |
| SMS | Twilio |
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
│   ├── campaigns/         # Campanhas de e-mail e SMS
│   ├── contacts/          # Contatos, grupos, importação CSV
│   ├── analytics/         # Métricas de campanhas
│   ├── documents/         # Gestão de documentos
│   ├── contracts/         # Gestão de contratos
│   └── thundertools/
│       ├── billing/       # Cobranças via Asaas
│       └── tasks/         # Gerenciamento de projetos (Kanban)
├── core/
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
├── templates/
├── static/
├── manage.py
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

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

TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx

ASAAS_API_KEY=$aact_xxxxxxxxxxxxxxxxxxxx
ASAAS_BASE_URL=https://sandbox.asaas.com/api/v3

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

### 5. Rodar Celery (em outro terminal)

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

## Módulos

### `accounts` — Autenticação e Organizações

- Registro, login e recuperação de senha
- Multi-tenant: cada usuário pertence a uma **Organização**
- Gerenciamento de membros com **permissões por módulo**
- Middleware `get_user_organization` e decorator `require_permission`

### `contacts` — Gestão de Contatos

- Criação e edição de contatos individuais
- **Grupos de contatos** com relação M2M
- **Importação via CSV** — colunas: `email`, `nome`, `telefone`
- Validação e remoção de e-mails inválidos

### `campaigns` — Campanhas de E-mail e SMS

- Criação de campanhas com seleção de grupo de contatos
- Envio em **lotes via Celery**
- **Templates** de e-mail reutilizáveis
- **Agendamento** de campanhas com calendário visual
- Suporte a **SMS via Twilio**

### `analytics` — Métricas

- Acompanhamento de campanhas enviadas por organização

### `documents` e `contracts`

- Gestão de documentos e contratos vinculados à organização

---

## ThunderTools

Suite de ferramentas integradas à plataforma.

### Cobranças (`billing`)

Módulo de cobranças usando a **API Asaas**.

- Criar cobranças (Pix, Boleto, Cartão de crédito)
- Exibir QR Code Pix e linha digitável do boleto
- Enviar link de pagamento por e-mail e SMS
- **Webhook** para atualização automática de status

**Configuração do webhook para testes locais (ngrok):**

```bash
ngrok http 8000
# URL no painel Asaas: https://xxxx.ngrok.io/billing/webhook/
```

Rodar o servidor apontado para `0.0.0.0`:

```bash
python manage.py runserver 0.0.0.0:8000
```

Atualizar `settings.py`:

```python
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'xxxx.ngrok.io']
CSRF_TRUSTED_ORIGINS = ['https://xxxx.ngrok.io']
```

### Tarefas (`tasks`)

Módulo de gerenciamento de projetos estilo Asana.

- Criação de **projetos** e **tarefas**
- **Kanban** com drag-and-drop (A Fazer / Em Andamento / Concluído)
- Tarefas com título, descrição, prioridade, data de entrega e responsável
- **Comentários** por tarefa
- **Notificação por e-mail** ao atribuir tarefa
- **Celery Beat**: lembrete diário às 8h para tarefas com vencimento no dia

---

## Deploy (Railway)

O projeto está em produção no Railway conectado ao branch `main`.

```bash
# Trabalhe em develop
git checkout develop
git add .
git commit -m "feat: nova funcionalidade"
git push origin develop

# Quando pronto para produção:
git checkout main
git merge develop
git push origin main   # Railway faz deploy automático
```

**Variáveis de ambiente necessárias no Railway:**

```
ALLOWED_HOSTS=thundermail.com.br,thundermail-production.up.railway.app
CSRF_TRUSTED_ORIGINS=https://thundermail.com.br,https://thundermail-production.up.railway.app
SITE_URL=https://thundermail.com.br
```

---

## Segurança

- Todas as chaves de API ficam em variáveis de ambiente (`.env` / Railway Variables)
- O arquivo `.env` está no `.gitignore`
- O `.env.docker` não deve conter chaves reais
- Em caso de vazamento de chave, revogue imediatamente no painel do provedor

---

## Licença

MIT — veja [LICENSE](LICENSE) para detalhes.
