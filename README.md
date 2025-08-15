# Cognix-AI RAG Platform

A full-stack Retrieval-Augmented Generation (RAG) chat platform that enables users to upload documents and have contextual conversations with AI models.

## Features

- **User Authentication**: Secure JWT-based authentication
- **Document Upload**: Support for PDF, DOCX, and TXT files
- **RAG Chat**: Contextual conversations based on uploaded documents
- **Multi-LLM Support**: OpenAI, Gemini, Groq, Mistral, and Ollama
- **Dual Database Architecture**: Platform database for auth, user databases for personal data
- **Vector Search**: FAISS-based similarity search for document chunks
- **Responsive UI**: Modern React interface with Tailwind CSS

## Architecture

### Backend (FastAPI)
- **API Layer**: RESTful endpoints with automatic documentation
- **Authentication**: JWT tokens with bcrypt password hashing
- **Document Processing**: Text extraction and chunking
- **Vector Storage**: FAISS for embeddings and similarity search
- **LLM Integration**: Pluggable provider architecture

### Frontend (Next.js)
- **React Components**: Modern UI with TypeScript
- **Styling**: Tailwind CSS for responsive design
- **State Management**: React Context for authentication
- **API Client**: Axios with interceptors for auth

### Database
- **Platform Database**: MongoDB for user authentication and configuration
- **User Databases**: Individual MongoDB instances for personal chat data
- **Vector Storage**: FAISS for document embeddings

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- MongoDB (local or Atlas)

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy environment file:
```bash
cp .env.example .env
```

5. Update `.env` with your MongoDB connection string and other settings

6. Start the server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Copy environment file:
```bash
cp .env.example .env.local
```

4. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## Environment Variables

### Backend (.env)
```env
# Platform Database
PLATFORM_MONGODB_URL=mongodb://localhost:27017
PLATFORM_DATABASE_NAME=cognix_platform

# Authentication
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# LLM Providers
DEFAULT_LLM_PROVIDER=openai
OLLAMA_BASE_URL=http://localhost:11434

# Vector Store
VECTOR_STORE_TYPE=faiss
VECTOR_STORE_PATH=./vector_stores

# File Upload
MAX_FILE_SIZE=10485760
ALLOWED_EXTENSIONS=pdf,docx,txt

# HuggingFace
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Cognix-AI
NEXT_PUBLIC_MAX_FILE_SIZE=10485760
NEXT_PUBLIC_ALLOWED_EXTENSIONS=pdf,docx,txt
```

## API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation.

## Deployment

### Backend (Render)
1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python main.py`
5. Add environment variables from `.env.example`

### Frontend (Render)
1. Create a new Static Site
2. Set build command: `npm run build`
3. Set publish directory: `out` (if using static export)
4. Add environment variables from `.env.example`

### Database (MongoDB Atlas)
1. Create a MongoDB Atlas cluster
2. Create a database user
3. Whitelist your application's IP addresses
4. Update `PLATFORM_MONGODB_URL` with your connection string

## Development

### Project Structure
```
cognix-ai/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── routers/             # API route handlers
│   ├── services/            # Business logic
│   ├── models/              # Pydantic models
│   ├── utils/               # Utilities and helpers
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js app router pages
│   │   ├── components/      # React components
│   │   └── lib/             # Utilities and API client
│   ├── package.json         # Node.js dependencies
│   └── tailwind.config.js   # Tailwind CSS configuration
└── README.md
```

### Adding New LLM Providers
1. Create a new provider class in `backend/services/llm_service.py`
2. Implement the `LLMProvider` interface
3. Add the provider to the `LLMService.providers` dictionary
4. Update validation in `backend/utils/validators.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.