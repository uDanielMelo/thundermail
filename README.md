# ⚡ ThunderMail

**Plataforma de e-mail marketing para pequenas empresas**

ThunderMail é uma solução completa para criação, disparo e gestão de campanhas de e-mail marketing, construída com Django e projetada para ser simples de usar e fácil de hospedar.

---

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Tecnologias](#tecnologias)
- [Arquitetura](#arquitetura)
- [Pré-requisitos](#pré-requisitos)
- [Instalação e Execução](#instalação-e-execução)
  - [Com Docker (recomendado)](#com-docker-recomendado)
  - [Sem Docker](#sem-docker)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Funcionalidades](#funcionalidades)
- [Contribuindo](#contribuindo)
- [Licença](#licença)

---

## Visão Geral

O ThunderMail permite que pequenas empresas gerenciem suas listas de contatos e disparem campanhas de e-mail de forma autônoma, sem depender de plataformas caras ou complexas. O envio é feito de forma assíncrona via Celery, garantindo que grandes volumes de e-mails não travem a aplicação.

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Framework Web | [Django 6.0](https://www.djangoproject.com/) |
| Banco de Dados | [PostgreSQL 16](https://www.postgresql.org/) |
| Fila de Tarefas | [Celery 5.6](https://docs.celeryq.dev/) |
| Message Broker | [Redis 7](https://redis.io/) |
| Serviço de E-mail | [Resend](https://resend.com/) |
| Containerização | [Docker](https://www.docker.com/) + [Docker Compose](https://docs.docker.com/compose/) |

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
│ PostgreSQL  │                        │    Resend    │
│  (Banco)    │                        │  (Envio de   │
└─────────────┘                        │   E-mails)   │
                                       └──────────────┘
```

O Django recebe as requisições da interface web, salva os dados no PostgreSQL e enfileira os disparos no Redis. O Celery consome essa fila em background e usa a API do Resend para fazer o envio efetivo dos e-mails.

---

## Pré-requisitos

**Com Docker:**
- [Docker](https://docs.docker.com/get-docker/) 20+
- [Docker Compose](https://docs.docker.com/compose/install/) v2+

**Sem Docker:**
- Python 3.12+
- PostgreSQL 16
- Redis 7
- Conta no [Resend](https://resend.com/) com uma API Key

---

## Instalação e Execução

### Com Docker (recomendado)

**1. Clone o repositório**
```bash
git clone https://github.com/uDanielMelo/thundermail.git
cd thundermail
```

**2. Configure as variáveis de ambiente**

Copie o arquivo de exemplo e preencha com suas credenciais reais:
```bash
cp .env.docker .env.docker.local
```

> ⚠️ Edite `.env.docker.local` com suas configurações antes de prosseguir.

**3. Suba os containers**
```bash
docker compose up --build
```

A aplicação estará disponível em: **http://localhost:8000**

**Para rodar em background:**
```bash
docker compose up --build -d
```

**Para parar os containers:**
```bash
docker compose down
```

---

### Sem Docker

**1. Clone o repositório**
```bash
git clone https://github.com/uDanielMelo/thundermail.git
cd thundermail
```

**2. Crie e ative um ambiente virtual**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

**3. Instale as dependências**
```bash
pip install -r requirements.txt
```

**4. Configure as variáveis de ambiente**

Crie um arquivo `.env` na raiz do projeto com base na seção [Variáveis de Ambiente](#variáveis-de-ambiente).

**5. Execute as migrações**
```bash
python manage.py migrate
```

**6. Inicie o servidor Django**
```bash
python manage.py runserver
```

**7. Inicie o worker Celery** (em outro terminal)
```bash
celery -A core worker --loglevel=info
```

---

## Variáveis de Ambiente

Crie um arquivo `.env` com as seguintes variáveis:
```env
# Django
SECRET_KEY=sua-secret-key-segura-aqui
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Banco de Dados
DB_NAME=thundermail
DB_USER=seu_usuario
DB_PASSWORD=sua_senha_segura
DB_HOST=localhost      # Use "db" se estiver rodando via Docker
DB_PORT=5432

# Resend (https://resend.com)
RESEND_API_KEY=re_sua_chave_aqui

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0   # Use "redis://redis:6379/0" no Docker
```

> 🔒 Nunca commite seu `.env` com credenciais reais no repositório.

Para gerar uma `SECRET_KEY` segura:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Estrutura do Projeto
```
thundermail/
├── apps/                  # Apps Django (módulos de negócio)
├── core/                  # Configuração central (settings, urls, celery)
├── static/                # Arquivos estáticos (CSS, JS, imagens)
├── templates/             # Templates HTML da interface
├── manage.py              # CLI do Django
├── requirements.txt       # Dependências Python
├── Dockerfile             # Imagem Docker da aplicação
├── docker-compose.yml     # Orquestração dos containers
├── .env.docker            # Variáveis de ambiente de exemplo
└── .gitignore
```

---

## Funcionalidades

- ✅ Gerenciamento de listas de contatos
- ✅ Criação e disparo de campanhas de e-mail
- ✅ Envio assíncrono via Celery (não bloqueia a interface)
- ✅ Integração com Resend para entrega confiável
- ✅ Interface web com Django Templates
- 🚧 Relatórios de abertura e cliques *(em desenvolvimento)*
- 🚧 Agendamento de campanhas *(em desenvolvimento)*

---

## Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir uma *issue* ou enviar um *pull request*.

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/minha-feature`)
3. Commit suas alterações (`git commit -m 'feat: adiciona minha feature'`)
4. Push para a branch (`git push origin feature/minha-feature`)
5. Abra um Pull Request

---

## Licença

Distribuído sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais informações.