# ⚡ ThunderMail

**Plataforma de comunicação e operações para pequenas e médias empresas**

ThunderMail nasceu como uma plataforma de e-mail marketing e evoluiu para um hub completo de operações — campanhas, contatos, contratos, integrações e ferramentas de negócio, tudo em um só lugar.

---

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Tecnologias](#tecnologias)
- [Arquitetura](#arquitetura)
- [Pré-requisitos](#pré-requisitos)
- [Instalação e Execução](#instalação-e-execução)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Funcionalidades](#funcionalidades)
- [ThunderTools](#thundertools)
- [Licença](#licença)

---

## Visão Geral

O ThunderMail permite que empresas gerenciem contatos, disparem campanhas de e-mail e SMS, assinem contratos eletronicamente e acompanhem métricas de marketing — sem depender de múltiplas plataformas. Tudo integrado, em português, focado no mercado brasileiro.

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Framework Web | Django 6.0 |
| Banco de Dados | PostgreSQL 16 |
| Fila de Tarefas | Celery 5.6 |
| Message Broker | Redis 7 |
| Serviço de E-mail | Resend |
| SMS | Twilio |
| Métricas | Google Analytics Data API |
| Containerização | Docker + Docker Compose |

---

## Arquitetura
```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   Django    │────▶│    Redis    │────▶│    Celery    │
│  (Web App)  │     │  (Broker)   │     │   (Worker)   │
└─────────────┘     └─────────────┘     └──────┬───────┘
       │                                        │
       ▼                                        ▼
┌─────────────┐                        ┌──────────────┐
│ PostgreSQL  │                        │ Resend/Twilio│
│  (Banco)    │                        │ (E-mail/SMS) │
└─────────────┘                        └──────────────┘
```

---

## Pré-requisitos

**Com Docker:**
- Docker 20+
- Docker Compose v2+

**Sem Docker:**
- Python 3.12+
- PostgreSQL 16
- Redis 7
- Conta no Resend com API Key

---

## Instalação e Execução

### Com Docker (recomendado)
```bash
git clone https://github.com/uDanielMelo/thundermail.git
cd thundermail
cp .env.docker .env.docker.local
docker compose up --build
```

Acesse: **http://localhost:8000**

### Sem Docker
```bash
git clone https://github.com/uDanielMelo/thundermail.git
cd thundermail
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Worker Celery (segundo terminal):
```bash
celery -A core worker --loglevel=info
```

---

## Variáveis de Ambiente
```env
# Django
SECRET_KEY=sua-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
SITE_URL=http://localhost:8000

# Banco de Dados
DB_NAME=thundermail
DB_USER=postgres
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432

# Resend
RESEND_API_KEY=re_sua_chave

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0

# Twilio (SMS)
TWILIO_ACCOUNT_SID=sua_sid
TWILIO_AUTH_TOKEN=seu_token
TWILIO_PHONE_NUMBER=+55...

# Google Analytics
GOOGLE_CLIENT_ID=seu_client_id
GOOGLE_CLIENT_SECRET=seu_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/integrations/google/callback/
```

---

## Funcionalidades

### 📬 E-mail Marketing
- Criação e disparo de campanhas de e-mail
- Envio assíncrono via Celery
- Agendamento de campanhas
- Unsubscribe automático com 1 clique
- Header `List-Unsubscribe` (RFC) compatível com Gmail e Outlook

### 📱 SMS Marketing
- Criação e disparo de campanhas de SMS via Twilio
- Integrado ao mesmo pipeline de contatos

### 👥 Gestão de Contatos
- Grupos de contatos
- Importação via CSV
- Validação de e-mails
- Controle de descadastro por contato

### 📅 Agendamentos
- Agendamento de campanhas por data e hora
- Execução automática via Celery Beat

### 📊 Analytics
- Logs de envio por campanha
- Taxa de sucesso e falhas
- Integração com Google Analytics GA4

### 🔗 Integrações
- Google Analytics (sessões, usuários, pageviews, bounce rate)
- YouTube *(em breve)*
- Instagram *(em breve)*

---

## ThunderTools

Ferramentas extras integradas ao ecossistema ThunderMail para operações do dia a dia.

### ✍️ Assinatura Eletrônica de Contratos
- Upload de contratos em PDF
- Envio para múltiplos signatários por e-mail
- Assinatura via desenho no canvas ou digitação
- Registro de IP, data, hora e user agent
- Geração de PDF final com página de auditoria completa
- Validade jurídica conforme MP 2.200-2/2001 e Lei 14.063/2020

*Mais ferramentas em breve.*

---

## Licença

Distribuído sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais informações.