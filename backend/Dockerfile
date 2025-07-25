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
FROM python:3.13-slim AS runtime

# 1 – base OS tools + Node 20.x + NGINX from NodeSource
RUN apt-get update && apt-get install -y curl gnupg build-essential nginx \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
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

# 8 Nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# 9 Expose only nginx
EXPOSE 80

# 10 – start everything
CMD ["sh", "-c", "\
    nginx && \
    node dist/server.js & \
    node dist/demoServer.js & \
    python -u facilitator/facilitator.py & \
    python -u x402_servers/x402_server.py & \
    python -u treasury/main.py & \
    wait"]


