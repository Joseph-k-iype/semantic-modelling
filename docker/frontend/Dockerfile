# docker/frontend/Dockerfile
# Multi-stage build for React frontend - FIXED for pnpm lockfile compatibility
# Path: docker/frontend/Dockerfile

# ===== Development Stage =====
FROM node:18-alpine as development

WORKDIR /app

# Install pnpm (use latest stable version)
RUN npm install -g pnpm@latest

# Copy package files
COPY package.json pnpm-lock.yaml* ./

# Install dependencies with lockfile regeneration if needed
RUN if [ ! -f pnpm-lock.yaml ]; then \
        echo "🔄 No pnpm-lock.yaml found, installing with pnpm..." && \
        pnpm install; \
    else \
        echo "📦 Installing dependencies from lockfile..." && \
        pnpm install --frozen-lockfile || \
        (echo "🔄 Lockfile incompatible, regenerating..." && \
         rm -f pnpm-lock.yaml && \
         pnpm install); \
    fi

# Copy source code
COPY . .

# Expose port
EXPOSE 5173

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:5173 || exit 1

# Run development server
CMD ["pnpm", "dev", "--host", "0.0.0.0", "--port", "5173"]

# ===== Build Stage =====
FROM node:18-alpine as builder

WORKDIR /app

# Install pnpm (use latest stable version)
RUN npm install -g pnpm@latest

# Copy package files
COPY package.json pnpm-lock.yaml* ./

# Install dependencies
RUN pnpm install --frozen-lockfile || \
    (echo "🔄 Lockfile incompatible, regenerating..." && \
     rm -f pnpm-lock.yaml && \
     pnpm install)

# Copy source code
COPY . .

# Build application
RUN pnpm build

# ===== Production Stage =====
FROM nginx:alpine as production

# Copy nginx configuration
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Create nginx cache directory
RUN mkdir -p /var/cache/nginx && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]