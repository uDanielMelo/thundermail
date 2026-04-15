# ⚡ ThunderMail

**Plataforma SaaS de e-mail marketing e automação para pequenas empresas**

> Django 6 · PostgreSQL · Celery · Redis · Resend · Twilio · Asaas · Docker · Railway

---

## 🗂️ Visão Geral

O ThunderMail é uma plataforma multi-tenant construída em Django que centraliza comunicação por e-mail, SMS, gestão de contatos, cobranças e gerenciamento de projetos em um único produto — o **ThunderTools**.

**Produção:** [https://thundermail.com.br](https://thundermail.com.br)
**Repositório:** [https://github.com/uDanielMelo/thundermail](https://github.com/uDanielMelo/thundermail)

---

## 🏗️ Stack Técnica

| Camada | Tecnologia |
|---|---|
| Backend | Django 6.0.3 |
| Banco de dados | PostgreSQL (psycopg3) |
| Fila de tarefas | Celery 5.6 + Redis |
| Agendamento | Celery Beat |
| E-mail transacional | Resend (SMTP) |
| SMS | Twilio |
| Pagamentos | Asaas (Pix, Boleto, Cartão) |
| Frontend | Django Templates + Tailwind CSS |
| Deploy | Railway (produção) |
| Containers | Docker + docker-compose |
| Ambiente local | Python venv + `.env` |

---

## 📁 Estrutura do Projeto

```
thundermail/
├── apps/
│   ├── accounts/          # Autenticação, organizações, membros, permissões
│   ├── campaigns/         # Campanhas de e-mail e SMS
│   ├── contacts/          # Contatos, grupos, importação CSV
│   ├── analytics/         # Métricas de campanhas
│   ├── documents/         # Módulo de documentos
│   ├── contracts/         # Módulo de contratos
│   └── thundertools/
│       ├── billing/       # ThunderTools Cobranças (Asaas)
│       └── tasks/         # ThunderTasks (Kanban / Asana-like)
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
└── .env.docker
```

---

## 🚀 Setup Local

### Pré-requisitos

- Python 3.11+
- PostgreSQL rodando localmente (ou via Docker)
- Redis rodando localmente (ou via Docker)
- Docker Desktop (opcional, para rodar tudo em container)

### 1. Clonar e criar ambiente virtual

```powershell
git clone https://github.com/uDanielMelo/thundermail.git
cd thundermail
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz com base no `.env.docker`:

```env
SECRET_KEY=sua_secret_key_aqui
DEBUG=True
DATABASE_URL=postgres://usuario:senha@localhost:5432/thundermail
REDIS_URL=redis://localhost:6379/0

# Resend (e-mail transacional)
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxx

# Twilio (SMS)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx

# Asaas (cobranças — use sandbox para testes)
ASAAS_API_KEY=$aact_xxxxxxxxxxxxxxxxxxxx
ASAAS_BASE_URL=https://sandbox.asaas.com/api/v3

# URL do site (para links em e-mails)
SITE_URL=http://localhost:8000
```

> ⚠️ **Nunca commite o `.env`** — ele está no `.gitignore`. O `.env.docker` é usado apenas para o Docker.

### 3. Migrations e superusuário

```powershell
python manage.py migrate
python manage.py createsuperuser
```

### 4. Rodar o servidor

```powershell
python manage.py runserver
```

### 5. Rodar Celery (em outro terminal)

```powershell
# Worker
celery -A core worker --loglevel=info --pool=solo

# Beat (agendamentos)
celery -A core beat --loglevel=info
```

### 6. Via Docker (alternativa)

```powershell
# Certifique-se de que o Docker Desktop está aberto
docker compose up --build
```

---

## 🐳 Docker Compose

O `docker-compose.yml` sobe os serviços: `web` (Django), `celery` (worker), `celery-beat`, `postgres` e `redis`.

Para produção, as variáveis são configuradas diretamente no Railway como Environment Variables.

---

## 📦 Módulos

### `accounts` — Autenticação e Organizações

- Registro e login de usuários
- Multi-tenant: cada usuário pertence a uma **Organização**
- Gerenciamento de **membros** com sistema de **permissões por módulo** (switches individuais)
- Recuperação de senha por e-mail (Django PasswordResetView + template HTML)
- Middleware `get_user_organization` e decorator `require_permission`

### `contacts` — Gestão de Contatos

- Listagem, criação e edição de contatos individuais
- **Grupos de contatos** com M2M (`Contact ↔ ContactGroup`)
- Abas separadas para **Emails** e **Telefones** no formulário de grupo
- Validação e remoção de e-mails inválidos (botão "Remover e-mails inválidos")
- **Importação via CSV**: colunas aceitas `email`, `nome`, `telefone`
  - Contatos somente-SMS usam placeholder `phone@sms.local` como e-mail
  - Vinculação automática de telefones via CSV ao grupo

### `campaigns` — Campanhas de E-mail e SMS

- Criação de campanhas com seletor de grupo (busca + contador de contatos)
- Envio em **lotes via Celery** para evitar timeout
- **Templates de e-mail** salvos e reutilizáveis
- Agendamento de campanhas com timezone correto
- Calendário visual de agendamentos com tooltip
- Suporte a campanhas de **SMS via Twilio**
- Integração com `send_campaign_email` para disparo transacional via Resend

### `analytics` — Métricas

- Acompanhamento de campanhas enviadas
- (Em desenvolvimento: webhooks do Resend para abertura/cliques)

### `documents` e `contracts`

- Módulos de gestão de documentos e contratos da organização

---

## ⚡ ThunderTools

Suite de ferramentas integradas acessíveis dentro da plataforma.

### 🧾 ThunderTools Cobranças (`billing`)

Módulo de cobranças usando a **API Asaas** (suporta contas sandbox).

**Funcionalidades:**
- Criar cobranças (Pix, Boleto, Cartão de crédito)
- Exibir **QR Code Pix** e **linha digitável do boleto**
- Enviar link de pagamento por **e-mail e SMS** ao criar a cobrança
- Dashboard de status das cobranças
- **Webhook** para atualização automática de status via Asaas

**Configuração do webhook (ngrok para testes locais):**
```bash
ngrok http 8000
# URL no Asaas: https://xxxx.ngrok.io/billing/webhook/
# (trailing slash obrigatório)
```

**Variáveis necessárias:**
```env
ASAAS_API_KEY=...
ASAAS_BASE_URL=https://sandbox.asaas.com/api/v3
```

**Atenção:** rodar o servidor com `0.0.0.0:8000` para o ngrok funcionar:
```powershell
python manage.py runserver 0.0.0.0:8000
```

E atualizar no `settings.py`:
```python
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'xxxx.ngrok.io']
CSRF_TRUSTED_ORIGINS = ['https://xxxx.ngrok.io']
```

---

### ✅ ThunderTasks (`tasks`)

Módulo de gerenciamento de projetos estilo Asana.

**Funcionalidades:**
- Criação de **projetos** e **tarefas**
- Kanban com **drag-and-drop** entre colunas (A Fazer / Em Andamento / Concluído)
- Tarefas com: título, descrição, prioridade, data de entrega, responsável
- **Comentários** por tarefa
- **Notificação por e-mail** ao atribuir uma tarefa a um membro
- **Celery Beat**: lembrete diário às 8h para tarefas com vencimento no dia

---

## 🌐 Deploy (Railway)

O projeto está em produção no Railway conectado ao branch `main`.

**Fluxo recomendado:**

```powershell
# Trabalhe sempre em develop
git checkout develop
# ... edita, testa local ...
git add .
git commit -m "feat: nova funcionalidade"
git push origin develop

# Quando pronto para produção:
git checkout main
git merge develop
git push origin main   # Railway faz deploy automático
```

**Variáveis de ambiente no Railway** (além das do `.env`):

```
ALLOWED_HOSTS=thundermail.com.br,thundermail-production.up.railway.app
CSRF_TRUSTED_ORIGINS=https://thundermail.com.br,https://thundermail-production.up.railway.app
SITE_URL=https://thundermail.com.br
```

---

## 📝 Padrão de Commits

```
feat      → novo recurso
fix       → correção de bug
docs      → documentação
test      → testes
build     → build/dependências
perf      → performance
style     → formatação (sem mudança de lógica)
refactor  → refatoração sem mudança funcional
chore     → tarefas de manutenção
ci        → integração contínua
raw       → arquivos de configuração / dados
cleanup   → remoção de código comentado/desnecessário
remove    → exclusão de arquivos ou funcionalidades
```

**Exemplos:**
```bash
git commit -m "feat(billing): webhook Asaas para atualização automática de status"
git commit -m "fix(contacts): corrigir importação de telefones via CSV"
git commit -m "refactor(contacts): M2M groups, sync por tipo, fix remoção ao editar"
```

---

## 🐛 Bugs Conhecidos / Pendências

| Módulo | Descrição | Status |
|---|---|---|
| contacts | Telefones importados via CSV não aparecem na aba Phones ao editar grupo | 🔴 Em aberto |
| analytics | Webhooks do Resend para tracking de abertura/cliques | ⏳ Pendente |
| deploy | Criar branch `staging` no Railway apontando para `develop` | ⏳ Pendente |

---

## 📋 Roadmap

- [ ] Webhooks do Resend (abertura e cliques de e-mail)
- [ ] Ambiente de staging no Railway (`develop` → `staging.thundermail.com.br`)
- [ ] Melhorias visuais gerais na interface
- [ ] Testes automatizados (unitários e de integração)
- [ ] Módulo de Analytics expandido (gráficos por campanha)

---

## 🔐 Segurança

- Todas as chaves de API ficam em variáveis de ambiente (`.env` / Railway Variables)
- O arquivo `.env` está no `.gitignore`
- O `.env.docker` **não deve conter chaves reais** — use apenas para referência local
- Em caso de vazamento de chave, revogue imediatamente no painel do provedor

---

## 📜 Licença

MIT — veja [LICENSE](LICENSE) para detalhes.