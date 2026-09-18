# Use a lightweight Node.js image
FROM node:20-alpine

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy package.json and package-lock.json first to leverage Docker cache
COPY package*.json ./

# Install dependencies (only production dependencies are needed for the API)
RUN npm ci --only=production

# Copy the rest of the backend source code
# CRITICAL: Ensure your .dockerignore file excludes .env and node_modules!
COPY . .

# Ensure the public directory exists so express.static doesn't crash if the frontend isn't built yet
RUN mkdir -p public

# Expose the port the app runs on
EXPOSE 3000

# Start the application
CMD ["node", "server.js"]