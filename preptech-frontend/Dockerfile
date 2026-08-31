# Etapa 1: Construcción de la aplicación web
FROM node:22-alpine AS builder
WORKDIR /app
RUN corepack enable
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm run build

# Etapa 2: Servidor Web Ultraligero (Nginx)
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html

# Copiamos nuestra configuración personalizada de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]