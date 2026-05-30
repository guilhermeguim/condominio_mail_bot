# 1. Imagem base minimalista do Python 3.11 otimizada para produção
FROM python:3.11-slim

# 2. Impedir que o Python crie ficheiros .pyc e forçar o output imediato no terminal (vital para lermos os logs no GCP)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Definir o diretório de trabalho dentro do contentor
WORKDIR /app

# 4. Copiar APENAS o manifesto primeiro (Estratégia de Cache do Docker)
COPY requirements.txt .

# 5. Instalar dependências sem guardar cache do pip para manter a imagem o mais leve possível
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar a totalidade do código fonte
COPY ./src ./src

# 7. Expor a porta 8080 (Porta padrão exigida e mapeada pelo Google Cloud Run)
EXPOSE 8080

# 8. Comando de arranque do nosso "rececionista" apontando para a porta 8080
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]