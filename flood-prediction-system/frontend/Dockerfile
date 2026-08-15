FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY vite.config.ts ./
COPY tsconfig*.json ./
COPY tailwind.config.js ./
COPY postcss.config.js ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Expose port (Vite dev server)
EXPOSE 5173

# Default command for development
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
