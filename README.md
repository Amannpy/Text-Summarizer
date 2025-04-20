# Text Summarizer API

A Flask-based API that provides text summarization capabilities with both abstractive and extractive methods, along with sentiment analysis and keyword extraction.

## Features

- User authentication with JWT
- Rate limiting (5 requests per minute)
- Multiple input formats support (text, PDF, DOCX, URL)
- Both abstractive and extractive summarization
- Sentiment analysis and keyword extraction
- Summary history storage
- Dockerized deployment

## Setup

### Using Docker (Recommended)

1. Clone the repository
2. Create a `.env` file with your configuration:
   ```
   DATABASE_URI=postgresql://postgres:password@db:5432/summarizer
   JWT_SECRET_KEY=your-secret-key-here
   ```
3. Build and run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

### Manual Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set up environment variables in `.env`
3. Initialize the database:
   ```bash
   flask init-db
   ```
4. Run the application:
   ```bash
   flask run
   ```

## API Endpoints

### Authentication

- POST `/register`
  - Register a new user
  - Body: `{"username": "user", "password": "pass", "email": "user@example.com"}`

- POST `/login`
  - Login and get JWT token
  - Body: `{"username": "user", "password": "pass"}`

### Summarization

- POST `/summarize`
  - Requires JWT Authentication
  - Rate limited to 5 requests per minute
  - Supports text, PDF, DOCX, or URL input
  - Body examples:
    ```json
    {"text": "Your text here", "mode": "abstractive"}
    {"url": "https://example.com/article", "mode": "extractive"}
    ```
  - Response includes:
    - Summary
    - Word count
    - Compression ratio
    - Sentiment analysis
    - Keywords

## Technologies Used

- Flask
- PostgreSQL
- JWT Authentication
- TextBlob for NLP
- Transformers (BART) for abstractive summarization
- TextRank for extractive summarization
- Docker for containerization