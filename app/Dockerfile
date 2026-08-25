FROM python:3.11-slim

WORKDIR /srv

# dependências primeiro (aproveita cache de camada do Docker)
COPY app/requirements.txt app/requirements.txt
RUN pip install --no-cache-dir -r app/requirements.txt

# código e dados necessários em runtime
COPY app/ app/
COPY finetuning/__init__.py finetuning/__init__.py
COPY finetuning/hospital_profile.py finetuning/hospital_profile.py
COPY finetuning/data_prep/ finetuning/data_prep/
COPY data/raw/ data/raw/

EXPOSE 8501

# índices e logs são reconstruídos/gravados em runtime dentro do container
# (armazenamento efêmero no Consumption plan do Container Apps — uploads de
# prontuário feitos durante a sessão não sobrevivem a um restart/scale-to-zero;
# ver limitação documentada em docs/relatorio.md)
CMD ["streamlit", "run", "app/streamlit_app.py", \
     "--server.port=8501", "--server.address=0.0.0.0", \
     "--server.headless=true", "--server.fileWatcherType=none"]
