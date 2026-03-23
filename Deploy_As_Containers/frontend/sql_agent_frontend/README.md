# React.js Frontend for SQL Agent

This project is a React.js frontend application built with Vite. It is designed to interact with the `/query` API of the SQL Agent backend. The application can be hosted as a static website on AWS S3 or deployed as a containerized application using AWS App Runner.

## Project Setup

### Prerequisites
- Node.js (v20.19+ or 22.12+)
  - Check your Node.js version:
    ```bash
    node --version
    ```
- npm or yarn
  - Check your npm version:
    ```bash
    npm --version
    ```
  - If using yarn, check its version:
    ```bash
    yarn --version
    ```
- `package.json` file
  - Ensure the `package.json` file exists in the project directory. This file contains the list of dependencies required for the project.
  - If the file is missing, you can create one by running:
    ```bash
    npm init -y
    ```
- AWS CLI (configured with appropriate permissions)
  - **Note**: AWS CLI is required only for deploying the application to S3. If you do not have AWS CLI installed, you can use the AWS Management Console to upload files manually.

### Installation
1. Navigate to the project directory:
   ```bash
   cd sql_agent_frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```

### Development
To start the development server:
```bash
npm run dev
```
The application will be available at `http://localhost:5173`.

### Build
To build the application for production:
```bash
npm run build
```
The build output will be in the `dist` directory.

## Deployment to AWS S3

### Step 1: Build the Application
Ensure the application is built for production:
```bash
npm run build
```

### Step 2: Create an S3 Bucket
1. Open the AWS Management Console and navigate to the S3 service.
2. Click **Create bucket**.
3. Provide a unique bucket name (e.g., `sql-agent-frontend`).
4. Choose the appropriate AWS region.
5. Uncheck **Block all public access** and acknowledge the warning to make the bucket public.
6. Click **Create bucket**.

### Step 3: Configure the Bucket for Static Website Hosting
1. Go to the **Properties** tab of the bucket.
2. Enable **Static website hosting**.
3. Set the **Index document** to `index.html`.
4. (Optional) Set the **Error document** to `index.html` for single-page applications.

### Step 4: Upload the Build Files
1. Navigate to the `dist` directory:
   ```bash
   cd dist
   ```
2. Use the AWS CLI to upload the files:
   ```bash
   aws s3 sync . s3://<your-bucket-name> --acl public-read
   ```

### Step 5: Add a Bucket Policy
To allow public access to the files in your S3 bucket, you need to add a bucket policy. This policy ensures that users can access the static website files.

#### Bucket Policy Example
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::sql-agent-frontend/*"
    }
  ]
}
```

#### Why This Policy is Needed
This bucket policy allows public read access to all objects in the bucket. It is required for hosting a static website so that users can access the files (e.g., `index.html`, CSS, JavaScript) directly from the browser.

#### Steps to Add the Policy
1. Go to the **Permissions** tab of your S3 bucket.
2. Under **Bucket Policy**, click **Edit**.
3. Paste the above policy into the editor.
4. Save the changes.

Ensure that the **Block Public Access** settings are disabled for this bucket to allow the policy to take effect.

### Step 6: Access the Website
1. Go to the **Properties** tab of the bucket.
2. Copy the **Endpoint** URL under **Static website hosting**.
3. Open the URL in your browser to access the application.

## Deployment to AWS App Runner

If static website hosting is not possible, you can deploy the React app as a containerized application using AWS App Runner. Follow these steps:

### Step 1: Create a Dockerfile
1. In the `sql_agent_frontend` directory, create a file named `Dockerfile` with the following content:

   ```dockerfile
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
   ```

### Step 2: Build and Push the Docker Image to AWS ECR
If you are using AWS CloudShell to build and push the Docker image to Amazon Elastic Container Registry (ECR), follow these steps:

#### Files to Upload to AWS CloudShell
You need to upload the following files to AWS CloudShell:
1. `Dockerfile`
2. All application files, including:
   - `package.json`
   - `package-lock.json`
   - `src/` directory
   - `public/` directory (including `index.html`)

Ensure the entire project directory is uploaded to AWS CloudShell.

#### Commands to Build and Push the Docker Image
1. Authenticate Docker to your ECR repository:
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT-ID>.dkr.ecr.us-east-1.amazonaws.com
   ```

2. Build the Docker image:
   ```bash
   docker build -t sql-agent-frontend .
   ```

3. Tag the Docker image for ECR:
   ```bash
   docker tag sql-agent-frontend:latest <ACCOUNT-ID>.dkr.ecr.us-east-1.amazonaws.com/sql-agent-frontend:latest
   ```

4. Push the Docker image to ECR:
   ```bash
   docker push <ACCOUNT-ID>.dkr.ecr.us-east-1.amazonaws.com/sql-agent-frontend:latest
   ```

Replace `<ACCOUNT-ID>.dkr.ecr.us-east-1.amazonaws.com` with your ECR repository URI if different.

Once the image is pushed, you can use it to deploy the application in AWS App Runner or other container services.

### Step 3: Deploy to AWS App Runner
1. Open the AWS Management Console and navigate to **App Runner**.
2. Click **Create Service**.
3. Choose **Container Registry** as the source and select **Docker Hub**.
4. Provide the image URI (e.g., `<your-dockerhub-username>/sql-agent-frontend:latest`).
5. Configure the service settings:
   - **Port**: Set the port to `80`, as specified in the Dockerfile.
   - Configure other settings like service name, auto-scaling, etc.
6. Deploy the service.

### Step 4: Access the Application
1. Once the deployment is complete, App Runner will provide a public URL for your application.
2. Open the URL in your browser to access the React app.

---

## File Overview

### `package.json`
- **Purpose**: Defines the project metadata, dependencies, and scripts for building and running the application.

### `index.html`
- **Purpose**: The entry point for the React application. It contains the root `div` where the React app is mounted.

### `src/main.jsx`
- **Purpose**: The main entry file for the React application. It renders the `App` component into the root `div` in `index.html`.

### `src/App.jsx`
- **Purpose**: The main React component that contains the application logic and UI. It includes:
  - A form to input queries.
  - Logic to send queries to the `/query` API.
  - Sections to display the API response or errors.

### `src/index.css`
- **Purpose**: Contains global styles for the application, such as font and layout settings.

## Notes
- Ensure CORS is configured on the S3 bucket to allow requests to the `/query` API.
- Monitor the browser console for any errors during API communication.

---

This completes the setup and deployment process for the React.js frontend application.
