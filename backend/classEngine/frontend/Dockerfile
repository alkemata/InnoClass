# Stage 1: install dependencies
FROM node:18-alpine
WORKDIR /app
COPY ./classEngine/frontend/package.json ./

RUN npm install
RUN npm tailwindcss postcss
RUN npm init vite@latest . -- --template react-ts
RUN npx tailwindcss init -p