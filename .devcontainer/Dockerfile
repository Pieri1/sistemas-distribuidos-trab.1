FROM mcr.microsoft.com/devcontainers/python:3.11

# Dependências do sistema operacional (Node.js e npm para o Frontend) e bibliotecas Python:
RUN apt-get update && apt-get install -y nodejs npm
RUN pip install --upgrade pika pycryptodome fastapi uvicorn requests python-dotenv
