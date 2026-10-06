FROM node:24-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci 
COPY . .
# Set default environment variables
ENV NODE_ENV=production
ENV PORT=5002
# Document that the container listens on port 5002
EXPOSE 5002
# Specify the command to run the registration service
CMD ["node", "index.js"]