FROM node:20-alpine

WORKDIR /app

# Enable hot reload polling inside containers if needed
ENV PORT=3000 \
    HOSTNAME="0.0.0.0"

# Install dependencies based on package-lock.json
COPY package.json package-lock.json ./
RUN npm ci

# Copy project files
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
