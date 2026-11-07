FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app
RUN useradd --uid 10001 --no-create-home app
COPY lab_service.py .
USER 10001

EXPOSE 8765

CMD ["python", "lab_service.py", "--bind", "0.0.0.0", "--port", "8765"]
