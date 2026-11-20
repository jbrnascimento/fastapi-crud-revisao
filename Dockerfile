
FROM python:3.12-slim

# Configurações do Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Diretório de trabalho
WORKDIR /app

# Instala as dependências
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Cria um usuário sem privilégios administrativos
RUN useradd --create-home appuser

# Copia os arquivos da aplicação
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser migrations/ ./migrations/
COPY --chown=appuser:appuser alembic.ini .

# Porta da API
EXPOSE 8000

# Executa como usuário não privilegiado
USER appuser

# Inicialização padrão: FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
