# Business Idea Generator

A complete full-stack application for generating creative business ideas using OpenAI's GPT model, featuring a FastAPI backend with streaming support and a modern Gradio web interface.

## 🏗️ Architecture

- **Backend (`/server`)**: FastAPI application with OpenAI integration and streaming support
- **Frontend (`/app`)**: Gradio web interface for user interaction
- **Deployment**: Docker Compose orchestration

## 📁 Project Structure

```
AI_In_Production/
├── app/                    # Gradio Frontend Application
│   ├── main.py            # Gradio interface
│   ├── requirements.txt   # Frontend dependencies
│   └── Dockerfile         # Frontend container
├── server/                # FastAPI Backend Application  
│   ├── main.py           # FastAPI server
│   ├── requirements.txt  # Backend dependencies
│   ├── Dockerfile        # Backend container
│   └── test_streaming.py # API testing script
├── .env                  # Environment variables
├── .gitignore           # Git ignore rules
├── docker-compose.yml   # Multi-service orchestration
└── README.md           # Project documentation
```

## 🚀 Deployment

### Prerequisites
- Docker and Docker Compose installed
- OpenAI API key configured in `.env` file

### Docker Compose (Recommended)
```bash
# Build and start all services
docker-compose up --build

# Run in detached mode
docker-compose up --build -d

# Stop services
docker-compose down
```

### Individual Docker Services
```bash
# Server (FastAPI)
docker build -t business-idea-api ./server --build-arg OPENAI_API_KEY=your_api_key_here
docker run -p 8000:8000 business-idea-api

# App (Gradio)
docker build -t business-idea-app ./app
docker run -p 7860:7860 -e FASTAPI_BASE_URL=http://localhost:8000 business-idea-app
```

### Access Applications
- 🎨 **Gradio Web Interface**: http://localhost:7860
- 🔧 **FastAPI Backend**: http://localhost:8000
- 📋 **API Documentation**: http://localhost:8000/docs

## 🎯 Features

### Backend (FastAPI)
✅ **Streaming Responses** - Real-time business idea generation  
✅ **RESTful API** - Clean, documented endpoints  
✅ **OpenAI Integration** - GPT-powered idea generation  
✅ **Environment Configuration** - Secure API key management  
✅ **Health Checks** - Monitoring and uptime verification  
✅ **CORS Support** - Frontend integration ready  

### Frontend (Gradio)
✅ **Modern Web Interface** - Intuitive user experience  
✅ **Real-time Streaming** - Live text generation display  
✅ **Parameter Customization** - Industry, audience, budget controls  
✅ **API Status Dashboard** - Connection monitoring  
✅ **Markdown Rendering** - Beautiful formatted output  
✅ **Responsive Design** - Works on all devices  

## 📊 API Endpoints

### Backend Server (Port 8000)
- `GET /` - API information and status
- `GET /health` - Health check endpoint  
- `POST /generate-business-idea` - **Streaming** business idea generation
- `POST /generate-business-idea-json` - Traditional JSON response
- `POST /quick-idea` - Quick idea with default parameters

### Frontend Interface (Port 7860)
- **API Status Tab** - Backend connectivity and status
- **Custom Generation** - Tailored business idea creation
- **Quick Ideas** - One-click idea generation

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
DEFAULT_AWS_REGION=ap-south-1
AWS_ACCOUNT_ID=753304423515
```

### Service Architecture
- **Frontend (Gradio)**: Port 7860
- **Backend (FastAPI)**: Port 8000
- **Network**: Internal Docker bridge network for service communication

## 🔍 Testing

Test the API endpoints directly:
```bash
# Test streaming endpoint
curl -X POST "http://localhost:8000/generate-business-idea" \
  -H "Content-Type: application/json" \
  -d '{
    "industry": "healthcare",
    "target_audience": "elderly population", 
    "budget_range": "medium startup cost",
    "additional_context": "focus on remote monitoring"
  }'

# Test quick idea
curl -X POST "http://localhost:8000/quick-idea"
```

Or run the included test script:
```bash
# From the server directory
python test_streaming.py
```
