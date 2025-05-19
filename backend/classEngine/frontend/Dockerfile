# Stage 1: install dependencies
FROM node:18-alpine AS deps
WORKDIR /app
COPY ./classEngine/frontend/package.json ./
RUN npm install
RUN npm init vite@latest . -- --template react-ts