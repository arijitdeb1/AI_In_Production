# Deploying `bedrock_sql_agent` to AWS App Runner as a Docker Container

This guide provides step-by-step instructions to deploy the `bedrock_sql_agent` application as a Docker container to AWS App Runner.

---

## Prerequisites

1. **AWS Account**: Ensure you have an active AWS account.
2. **AWS CLI**: Install and configure the AWS CLI with the necessary permissions to create and manage App Runner services.
3. **Docker**: Install Docker on your local machine.
4. **IAM Role**: Create an IAM role with the following permissions:
   - `apprunner:CreateService`
   - `apprunner:UpdateService`
   - `apprunner:DeleteService`
   - `ecr:GetAuthorizationToken`
   - `ecr:BatchCheckLayerAvailability`
   - `ecr:GetDownloadUrlForLayer`
   - `ecr:BatchGetImage`
   - `ecr:PutImage`
   - `ecr:CreateRepository`
   - `ecr:DescribeRepositories`
   - `ecr:DeleteRepository`
   - `ecr:ListImages`
   - `ecr:GetRepositoryPolicy`
   - `ecr:SetRepositoryPolicy`
   - `ecr:DeleteRepositoryPolicy`
5. **Docker Hub Account**: If you plan to use Docker Hub for hosting your container image.

---

## Steps to Deploy

### Step 1: Create a Dockerfile

1. Create a `Dockerfile` in the `container_deployment` directory with the following content:

```dockerfile
# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
# This line already copies global-bundle.pem if it's in your current folder
COPY . .

# Expose port 8000 for the FastAPI app
EXPOSE 8000

# Command to run the FastAPI app
CMD ["uvicorn", "bedrock_sql_agent:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. Save the file in the `container_deployment` directory.

3. Proceed to Step 2 to build the Docker image.

### Step 2: Build and Test the Docker Image

1. Build the Docker image:
   ```bash
   docker build -t bedrock-sql-agent .
   ```

   Note: For secure database connectivity, you can specify `sslmode` and `sslrootcert` parameters in your database connection configuration. Ensure that the required certificate file (e.g., `.pem` file) is included in your project directory. This file will be bundled into the Docker image during the build process. Inside the container, provide the certificate's path as the value for `sslrootcert`. Refer to the example environment variables below:
   ```
      DB_SSLMODE=verify-full
      DB_SSLROOTCERT=/app/global-bundle.pem
   ```   

2. Ensure that the Docker image is built successfully and verify the image by listing it:
   ```bash
   docker images | findstr bedrock-sql-agent
   ```
   This command will display the `bedrock-sql-agent` image along with its tag and size.

3. Run the Docker container locally to ensure it works as expected:
   ```bash
   docker run -p 8000:8000 bedrock-sql-agent
   ```

### Step 3.1: Pass Environment Variables for Local Testing

You can pass environment variables to the Docker container during local testing using one of the following methods:

#### Option 1: Pass Variables Individually
Use the `--env` flag to pass each variable explicitly and run the container in detached mode:
```bash
docker run -d -p 8000:8000 \
  --env DB_HOST=localhost \
  --env DB_NAME=contract_api \
  --env DB_USER=contract_user \
  --env DB_PASS=contract_pass \
  --env DB_PORT=5432 \
  bedrock-sql-agent
```

#### Option 2: Use an `.env` File
If you have an `.env` file with all the required variables, you can pass them using the `--env-file` flag and run the container in detached mode:
```bash
docker run -d -p 8000:8000 --env-file c:\project\AI\LangChain_v1\sql_agent\.env bedrock-sql-agent
```

Ensure the `.env` file contains all the required variables, such as:
```dotenv
DB_HOST=localhost
DB_NAME=contract_api
DB_USER=contract_user
DB_PASS=contract_pass
DB_PORT=5432
```

4. Open your browser and navigate to `http://localhost:8000/health` to verify the health check endpoint.

Test `/query` endpoint 
```
    curl -X POST http://localhost:8000/query \
    -H "Content-Type: application/json" \
    -d '{"question": "What are all the schemas in the database?", "thread_id": "12345"}'
```

5. Proceed to Step 3 to push the Docker image to a container registry.



### Step 3: Push the Docker Image to a Container Registry

1. Authenticate Docker with AWS Elastic Container Registry (ECR):
   ```bash
   aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.<your-region>.amazonaws.com
   ```

2. Create a new ECR repository (if not already created):
   ```bash
   aws ecr create-repository --repository-name bedrock-sql-agent
   ```

3. Tag your Docker image for ECR:
   ```bash
   docker tag bedrock-sql-agent:latest <your-account-id>.dkr.ecr.<your-region>.amazonaws.com/bedrock-sql-agent:latest
   ```

4. Push the Docker image to ECR:
   ```bash
   docker push <your-account-id>.dkr.ecr.<your-region>.amazonaws.com/bedrock-sql-agent:latest
   ```

### Step 4: Deploy to AWS App Runner

1. Open the [AWS Management Console](https://aws.amazon.com/console/).
2. Navigate to **App Runner**.
3. Click on **Create service**.
4. Select **Container registry** as the source.
5. Choose **Amazon ECR** and select the `bedrock-sql-agent` repository.
6. Select the `latest` tag for the image.
7. Configure the service:
   - **Service name**: `bedrock-sql-agent`
   - **Port**: `8000`
   - **Auto scaling**: Configure as per your requirements.
8. Click **Next** and review the settings.
9. Click **Create and deploy**.

### Step 5: Verify the Deployment

1. Once the deployment is complete, note the **Default domain** provided by App Runner.
2. Open the default domain in your browser and navigate to `/health` to verify the health check endpoint.
3. Test the `/query` endpoint by sending a POST request with the required payload using a tool like Postman or `curl`.

Example `curl` command:
```bash
curl -X POST <app-runner-url>/query \
-H "Content-Type: application/json" \
-d '{"question": "What is the total sales?", "thread_id": "12345"}'
```

---

### Step 6: Troubleshooting
1. If the target database is within a private VPC and subnet, the connection may not establish as expected unless the following setup is in place:

- Navigate to the App Runner **Configuration** and go to **Networking**.
- Under **Outgoing network traffic**, select **Custom VPC**, then click **Add New** and provide the following details:
  - **VPC connector name**: Enter a unique name (e.g., `my-vpc-connector`).
  - **VPC**: Choose the target Amazon VPC from the dropdown list. Ensure it is the same VPC where the database resides.
  - **Subnets**: Select at least one private subnet for each Availability Zone you plan to access. For high availability, it is recommended to select three subnets. Ensure these subnets are the ones used by the database.
  - **Security groups**: Choose one or more security groups to associate with the connector’s network interfaces. These groups should have outbound rules allowing traffic to your destination resources.
- Additionally, add an **Inbound Rule** to the database's Security Group to allow traffic from the App Runner service. Use the following settings:
  - **Type**: `PostgreSQL`
  - **Protocol**: `TCP`
  - **Port range**: `5432`
  - **Source**: `Custom`, `0.0.0.0/0`, or the security group of the App Runner service.

2. If your code attempts to invoke a Bedrock Foundation model, such as Claude Sonnet, using its inference profile and encounters `NoCredentialsError` or similar errors:

- **Root Cause**: This issue arises because, while the VPC Connector manages the network path to RDS, it does not provide identity credentials for your code to access the Amazon Bedrock API.

- **Solution**: Set up an **Instance Role** for your App Runner service by following these steps:

  1. Navigate to the IAM Console Roles page and click **Create role**.

  2. **Trusted Entity**: Select **Custom trust policy** and paste the following policy to allow App Runner to use this role:
     ```json
     {
       "Version": "2012-10-17",
       "Statement": [
         {
           "Effect": "Allow",
           "Principal": {
             "Service": "tasks.apprunner.amazonaws.com"
           },
           "Action": "sts:AssumeRole"
         }
       ]
     }
     ```

  3. **Add Permissions**: Attach a policy that grants access to Bedrock. For testing, you can use the AWS-managed `AmazonBedrockFullAccess` policy, or create a more restrictive custom policy, such as:
     ```json
     {
       "Version": "2012-10-17",
       "Statement": [
         {
           "Effect": "Allow",
           "Action": [
             "bedrock:InvokeModel",
             "bedrock:InvokeModelWithResponseStream"
           ],
           "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-sonnet-*"
         }
       ]
     }
     ```

  4. **Name the Role**: Assign a name to the role, such as `AppRunner-Bedrock-Access-Role`.

  5. **Update App Runner Configuration**: Navigate to your service in the App Runner Console.

  6. Select **Configuration** -> **Security**.

  7. Under **Instance Role**, choose the `AppRunner-Bedrock-Access-Role` you just created.

  8. Save the changes and wait for the service to redeploy.

3. Encountering `Timed Out` errors, unresponsive App Runner services, or `NameResolutionError`, which indicates that your **App Runner** service lacks DNS access to the outside world:

- **Root Causes**:
  - **VPC Internet Access (Bedrock Connection)**: While the VPC Connector allows traffic into the VPC (e.g., to your RDS), it does not enable access to public AWS endpoints like the Amazon Bedrock API. To establish this connection, your VPC subnets must have a route to the internet via a NAT Gateway. Without this, calls to Bedrock will hang until they time out.
  - **App Runner Timeout Limits**: App Runner enforces a hard request timeout of 120 seconds. If Claude takes too long to respond (e.g., for a "list schemas" query involving both database and LLM processing), the service may terminate the connection, leaving the internal database session in a "half-open" state.
  - **Database Connection Exhaustion**: When the `/query` API hangs and fails, it may not properly close the SQLAlchemy connection. Each new attempt consumes another connection, eventually exhausting the pool. At this point, even `/health` (which likely checks the database) will fail to respond.

- **Fix**: Create an **Interface VPC Endpoint** for Bedrock. This ensures your App Runner service can communicate with Bedrock without leaving the AWS private network.
  1. Navigate to the **VPC Console** -> **Endpoints**.
  2. Click **Create endpoint**.
  3. **Service category**: Select AWS services.
  4. **Services**: Search for `bedrock-runtime` (ensure it matches your region, e.g., `us-east-1`).
  5. **VPC**: Choose the same VPC used by your RDS and App Runner.
  6. **Subnets**: Select the same subnets used by your VPC Connector.
  7. **Security Group**: Ensure the Security Group allows inbound HTTPS (Port 443) traffic from the App Runner VPC Connector Security Group.

- Additional Steps:
  1. Verify in the **VPC Endpoints Console** that **Private DNS names enabled** is set to `Yes`.
  2. In the **VPC Console**, select your VPC and confirm that both **DNS resolution** and **DNS hostnames** are `Enabled`.

- **The Full Traffic Flow**:
  1. **App Runner** sends a request to **Bedrock**.
  2. The **VPC Connector** routes this request into your VPC.
  3. The request reaches the **VPC Endpoint** on Port 443.
  4. The **Endpoint Security Group** evaluates the rule: "Is this request coming from the App Runner Security Group?"
  5. If **Yes**, the request is forwarded to the Bedrock service.

  **Pro Tip**: Ensure the **Outbound Rules** of your **VPC Connector Security Group** allow HTTPS (Port 443) traffic to either `0.0.0.0/0` or specifically to the VPC Endpoint's Security Group.
