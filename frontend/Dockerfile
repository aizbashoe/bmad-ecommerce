# syntax=docker/dockerfile:1
FROM node:22-slim

WORKDIR /app

# Install deps first for layer caching; npm ci uses the committed lockfile (reproducible).
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

# Vite dev server, bound to 0.0.0.0 so it's reachable from the host.
CMD ["npm", "run", "dev"]
