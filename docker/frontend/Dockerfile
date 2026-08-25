# Stage 1: Build React Application
FROM node:20-alpine AS builder

WORKDIR /app/frontend

# Copy dependency manifests
COPY frontend/package*.json ./

# Install npm dependencies
RUN npm ci

# Copy frontend source code
COPY frontend/ ./

# Set API base URL to empty so React uses relative URLs through Nginx proxy
ENV VITE_API_BASE_URL=""

# Build production React bundle
RUN npm run build

# Stage 2: Serve Production Bundle with Nginx
FROM nginx:alpine

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy build artifacts from Stage 1
COPY --from=builder /app/frontend/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Expose HTTP port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
