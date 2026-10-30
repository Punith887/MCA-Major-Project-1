FROM node:22-alpine

WORKDIR /app
ARG VITE_API_BASE_URL=http://localhost:8000/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

COPY package*.json ./
RUN npm ci --no-audit --no-fund

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev"]
