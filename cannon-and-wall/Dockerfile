FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install openenv flask fastapi uvicorn httpx gradio requests bandit
EXPOSE 7860
CMD ["openenv", "run", "--port", "7860"]
