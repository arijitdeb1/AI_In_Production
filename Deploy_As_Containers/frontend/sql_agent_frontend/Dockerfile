# Use an official Node.js runtime with a compatible version for Vite
   FROM node:20-alpine AS build

   # Set the working directory in the container
   WORKDIR /app

   # Copy package.json and package-lock.json
   COPY package*.json ./

   # Install dependencies
   RUN npm install

   # Copy the rest of the application code
   COPY . .

   # Build the React app
   RUN npm run build

   # Use an official Nginx image to serve the build files
   FROM nginx:alpine

   # Copy the build output to Nginx's default HTML directory
   COPY --from=build /app/dist /usr/share/nginx/html

   # Expose port 80
   EXPOSE 80

   # Start Nginx
   CMD ["nginx", "-g", "daemon off;"]
