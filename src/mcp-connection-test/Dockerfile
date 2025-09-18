FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json ./

# Copy test script
COPY test-connections.js ./

# Make the script executable
RUN chmod +x test-connections.js

# Run as non-root user
USER node

# Default command
CMD ["npm", "test"]