# ──────────────────────────────────────────────
# Stage 1 – build TS
# ──────────────────────────────────────────────
FROM node:20 AS builder
WORKDIR /app
COPY package.json tsconfig.json ./
COPY src ./src
RUN npm install && npm run build

# ──────────────────────────────────────────────
# Stage 2 – Python + Node runtime
# ──────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# 1 – base OS tools
RUN apt-get update && apt-get install -y \
    curl build-essential nodejs \
    && apt-get clean

# 2 – Python tooling
RUN pip install --no-cache-dir uv kaleido==0.2.0

# 3 – workdir
WORKDIR /app

# 4 – lockfiles, *then* deps from PyPI
COPY pyproject.toml pyproject.lock ./
RUN uv pip sync --system pyproject.lock

# 5 – copy **entire** backend source tree
COPY . .

# 6 – install your local package now that it’s present
RUN pip install --no-cache-dir -e .

# 7 – bring in built JS from the Node stage
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules

# 8 – ports
EXPOSE 5089 3000 4021 5074 5036

# 9 – start everything
CMD ["sh", "-c", "\
    node dist/server.js & \
    node dist/demoServer.js & \
    python -u facilitator/facilitator.py & \
    python -u x402_servers/x402_server.py & \
    python -u treasury/main.py & \
    wait"]


