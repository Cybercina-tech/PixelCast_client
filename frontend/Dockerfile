# Production image — build from repository root:
#   docker build -f frontend/Dockerfile .
#
# Stage 1: Build the Vue.js application
FROM node:20-alpine AS builder

WORKDIR /app

RUN apk add --no-cache git

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .

# Bake same-origin API paths into the SPA. Nginx proxies /api and /iot to Django (see nginx.conf).
# Never use https://backend:8000 here — that hostname exists only inside Docker networks; the browser cannot resolve it.
ARG VITE_API_BASE_URL=/api
ARG VITE_IOT_BASE_URL=/iot
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_IOT_BASE_URL=$VITE_IOT_BASE_URL

RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

RUN apk add --no-cache wget

COPY --from=builder /app/dist /usr/share/nginx/html

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
