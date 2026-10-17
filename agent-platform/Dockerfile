# ===========================================================================
# AgentOS
# ===========================================================================
FROM agnohq/python:3.14

# ---------------------------------------------------------------------------
# Application dependencies
# ---------------------------------------------------------------------------
WORKDIR /app
ENV PYTHONPATH=/app
COPY requirements.txt ./
RUN uv pip sync requirements.txt --system

# Copy only reviewed runtime code. Do not copy the repository context, local
# environment files, caches, databases, tests, or developer tooling.
COPY agents ./agents
COPY app ./app
COPY db ./db
COPY evals ./evals
COPY teams ./teams
COPY workflows ./workflows
COPY scripts/entrypoint.sh ./scripts/entrypoint.sh

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
RUN chmod +x /app/scripts/entrypoint.sh
ENTRYPOINT ["/app/scripts/entrypoint.sh"]

# ---------------------------------------------------------------------------
# Default command (overridden by compose for dev)
# ---------------------------------------------------------------------------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
