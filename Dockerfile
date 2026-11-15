# StackWatch simulator image (SW-15). Secrets come from Kubernetes at runtime, never baked in.
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir "requests>=2.31,<3" "PyYAML>=6,<7"
COPY simulator/ simulator/
COPY customers.yaml .
COPY splunk_app/stackwatch/lookups/stackwatch_plans.csv splunk_app/stackwatch/lookups/
RUN useradd --uid 10001 --no-create-home sim
USER 10001
ENV PYTHONUNBUFFERED=1 HEARTBEAT_FILE=/tmp/heartbeat
CMD ["python", "-m", "simulator"]
