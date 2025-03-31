FROM python:3.13-slim-bookworm

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# Install application
ADD . /app
WORKDIR /app
RUN uv sync --frozen

# Set default environment variables
ENV ZOTERO_LOCAL=false
ENV ZOTERO_API_KEY=""
ENV ZOTERO_LIBRARY_ID=""
ENV ZOTERO_LIBRARY_TYPE="user"

# Expose port 8000, standard for MCP
EXPOSE 8000

# Command to run the server
CMD ["uv", "run", "zotero-mcp", "--transport", "sse"]
