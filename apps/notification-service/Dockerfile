FROM node:24-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY . .

ENV NODE_ENV=production
ENV PORT=8005
EXPOSE 8005

CMD ["node", "server.js"]
