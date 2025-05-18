# Stage 1: install dependencies
FROM node:18-alpine AS deps
WORKDIR /app
COPY ./classEngine/frontend/package.json ./
RUN npm install

# Stage 2: dev environment
FROM node:18-alpine AS dev
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Expose Vite default port
EXPOSE 5173
CMD ["npm", "run", "dev"]