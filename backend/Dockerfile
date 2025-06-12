# Stage 1: Install deps & build TypeScript
FROM node:20 AS builder

WORKDIR /app

# Install Node deps
COPY package.json tsconfig.json ./
COPY src ./src
RUN npm install
RUN npm run build

# Stage 2: Final image with Python and Node runtime
FROM python:3.11-slim AS runtime

# Set working directory
WORKDIR /app

# Copy Python app
COPY requirements.txt .
COPY ccip_terminal ./ccip_terminal
COPY httpayer ./httpayer
COPY abi ./abi
COPY src/facilitator.py ./src/facilitator.py
COPY src/main.py ./src/main.py

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy built Node.js app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY .env .

# Optional: Expose Flask + Node ports
EXPOSE 5089 3000 4021

# Default entrypoint (override via docker-compose or CLI)
CMD ["sh", "-c", "python src/main.py & node dist/server.js"]
