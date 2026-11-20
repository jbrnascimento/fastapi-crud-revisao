# API de Gerenciamento de Tarefas

API REST desenvolvida em Python com FastAPI, PostgreSQL e SQLAlchemy assíncrono. O projeto implementa gerenciamento de usuários e tarefas, autenticação JWT com Access Token e Refresh Token, além de processamento de tarefas em segundo plano utilizando Celery e RabbitMQ.

O projeto utiliza uma arquitetura organizada em camadas, migrações de banco de dados com Alembic e conteinerização com Docker Compose.

## Tecnologias utilizadas

- **Python 3.12**
- **FastAPI** – desenvolvimento da API REST.
- **Uvicorn** – servidor ASGI.
- **PostgreSQL 16** – banco de dados relacional.
- **SQLAlchemy 2** – ORM utilizado com suporte a operações assíncronas.
- **asyncpg** – driver assíncrono para PostgreSQL.
- **Alembic** – controle de versões e migrações do banco.
- **Pydantic 2** – validação e serialização de dados.
- **PyJWT** – geração e validação de tokens JWT.
- **pwdlib + Argon2** – proteção de senhas.
- **Celery 5** – processamento de tarefas em segundo plano.
- **RabbitMQ 4** – broker de mensagens.
- **Docker e Docker Compose** – conteinerização e gerenciamento dos serviços.

## Funcionalidades

### 1. Gerenciamento de usuários

- Cadastro de usuários.
- Consulta de usuários.
- Listagem de usuários.
- Atualização parcial de dados.
- Exclusão de usuários.
- Validação de e-mail duplicado.

### 2. Gerenciamento de tarefas

- Criação de tarefas.
- Listagem das tarefas do usuário autenticado.
- Consulta de tarefa por identificador.
- Atualização parcial de tarefas.
- Exclusão de tarefas.
- Associação das tarefas aos respectivos usuários.

As operações de tarefas exigem autenticação JWT e respeitam o usuário autenticado.

### 3. Autenticação e segurança

- Autenticação por e-mail e senha utilizando formulário OAuth2.
- Geração de Access Token e Refresh Token.
- Armazenamento dos Refresh Tokens como hash no banco de dados.
- Validação de assinatura e expiração dos tokens.
- Renovação dos tokens com rotação do Refresh Token.
- Revogação de tokens anteriores.
- Logout com revogação do Refresh Token.
- Senhas protegidas com Argon2.

As rotas de usuários não exigem autenticação JWT nesta versão do projeto.

### 4. Processamento em segundo plano

Integração entre FastAPI, Celery, RabbitMQ e PostgreSQL.

A aplicação permite enviar tarefas para processamento assíncrono e consultar posteriormente seu estado e resultado.

A função de demonstração implementada realiza uma operação de soma de dois números inteiros.

### 5. Banco de dados

- PostgreSQL.
- SQLAlchemy com operações assíncronas.
- Separação lógica pelo schema `fastapi_crud`.
- Migrações gerenciadas pelo Alembic.

## Arquitetura do projeto

```text
fastapi_crud_revisao/
├── app/
│   ├── __init__.py
│   ├── core/
│   │   ├── auth.py
│   │   └── security.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── refresh_token_repository.py
│   │   ├── task_repository.py
│   │   └── user_repository.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── celery_tasks.py
│   │   ├── tasks.py
│   │   └── users.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   ├── task_service.py
│   │   └── user_service.py
│   ├── celery_app.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   └── tasks.py
├── migrations/
│   ├── versions/
│   │   ├── 26a4fb6118ce_create_tasks_table.py
│   │   ├── 789ffe10d209_cascade_em_tasks_user_id.py
│   │   ├── 7f9a9fde3797_create_refresh_tokens_table.py
│   │   ├── eea25d8ed71a_add_password_to_users.py
│   │   └── fd5d6b810c5c_test_schema_detection.py
│   ├── env.py
│   ├── README
│   └── script.py.mako
├── tests/
│   ├── conftest.py
│   ├── test_app.py
│   ├── test_auth.py
│   └── test_security.py
├── .dockerignore
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── README.md
└── requirements.txt
```

### Organização em camadas

- **routers:** recebem as requisições HTTP e encaminham as operações.
- **services:** concentram as regras de negócio.
- **repositories:** executam as operações de acesso aos dados.
- **core:** contém funcionalidades relacionadas à autenticação e segurança.
- **models.py:** define os modelos do banco de dados.
- **schemas.py:** define os schemas de entrada e saída.
- **celery_app.py:** configura o processamento assíncrono.
- **tasks.py:** contém as tarefas executadas pelo Celery.
- **migrations:** contém as migrações do banco de dados.

## Endpoints

### Usuários

| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/users` | Cadastrar usuário |
| GET | `/users` | Listar usuários |
| GET | `/users/{user_id}` | Consultar usuário |
| PATCH | `/users/{user_id}` | Atualizar usuário |
| DELETE | `/users/{user_id}` | Excluir usuário |

### Tarefas

| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/tasks` | Criar tarefa |
| GET | `/tasks` | Listar tarefas |
| GET | `/tasks/{task_id}` | Consultar tarefa |
| PATCH | `/tasks/{task_id}` | Atualizar tarefa |
| DELETE | `/tasks/{task_id}` | Excluir tarefa |

Todas as rotas de tarefas exigem autenticação JWT.

### Autenticação

| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/auth/token` | Login e geração dos tokens |
| POST | `/auth/refresh` | Renovar os tokens |
| POST | `/auth/logout` | Revogar Refresh Token |

### Tarefas em segundo plano

| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/background-tasks/somar` | Solicitar execução da soma |
| GET | `/background-tasks/{task_id}` | Consultar execução e resultado |

### Outros

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/` | Mensagem de funcionamento |
| GET | `/health` | Verificação de saúde da API |

## Execução com Docker Compose

### Pré-requisitos

- Docker Desktop.
- Docker Compose.
- Git.

### 1. Clonar o repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd fastapi_crud_revisao
```

### 2. Configurar as variáveis de ambiente

Crie um arquivo `.env.docker` na raiz do projeto.

Configure as variáveis necessárias para:

- PostgreSQL.
- URL de conexão do banco de dados.
- Chave secreta JWT.
- Algoritmo e tempos de expiração dos tokens.
- Credenciais do RabbitMQ.
- URL do broker Celery.
- Backend de resultados do Celery.

Utilize credenciais próprias e fortes. Não compartilhe esse arquivo nem o envie ao GitHub.

### 3. Construir as imagens

```bash
docker compose --env-file .env.docker build
```

### 4. Iniciar os serviços

```bash
docker compose --env-file .env.docker up -d
```

O Docker Compose inicia os seguintes serviços:

- API FastAPI.
- PostgreSQL.
- RabbitMQ.
- Worker Celery.

A API executa as migrações do Alembic antes de iniciar o servidor.

### 5. Verificar os serviços

```bash
docker compose --env-file .env.docker ps
```

Consultar os logs:

```bash
docker compose --env-file .env.docker logs -f api
```

Para consultar o worker:

```bash
docker compose --env-file .env.docker logs -f worker
```

### 6. Acessar a documentação

Com os serviços em execução:

- API: http://localhost:8001
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc
- Health check: http://localhost:8001/health

## Testes

O projeto possui testes automatizados com pytest.

Para executar os testes no ambiente Python local:

```bash
python -m pytest -v
```

## Considerações sobre segurança

- Credenciais e chaves secretas devem ser fornecidas por variáveis
  de ambiente.
- Arquivos `.env` e `.env.*` estão protegidos pelo `.gitignore`.
- Senhas são armazenadas utilizando hash Argon2.
- Refresh Tokens são armazenados como hash.
- Operações sobre tarefas são vinculadas ao usuário autenticado.

## Objetivo do projeto

Projeto desenvolvido para consolidar e demonstrar conhecimentos em desenvolvimento de APIs REST com Python, arquitetura em camadas, programação assíncrona, persistência de dados, autenticação e processamento distribuído de tarefas.