import pytest
from app import app, db
from models import User
import json
from transformers import pipeline

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

@pytest.fixture
def auth_headers(client):
    # Register a test user
    client.post('/register', json={
        'username': 'testuser',
        'password': 'testpass',
        'email': 'test@example.com'
    })
    
    # Login to get JWT token
    response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    token = json.loads(response.data)['access_token']
    return {'Authorization': f'Bearer {token}'}

def test_register(client):
    response = client.post('/register', json={
        'username': 'newuser',
        'password': 'newpass',
        'email': 'new@example.com'
    })
    assert response.status_code == 201
    assert b'User created successfully' in response.data

def test_login(client):
    # First register a user
    client.post('/register', json={
        'username': 'loginuser',
        'password': 'loginpass',
        'email': 'login@example.com'
    })
    
    # Then try to login
    response = client.post('/login', json={
        'username': 'loginuser',
        'password': 'loginpass'
    })
    assert response.status_code == 200
    assert 'access_token' in json.loads(response.data)

# Initialize the summarization pipeline
summarizer = pipeline("summarization")

def test_summarize_text(client, auth_headers):
    response = client.post('/summarize', 
        headers=auth_headers,
        json={
            'text': 'This is a test text that needs to be summarized. It contains multiple sentences with various information. The summary should be shorter than the original text.',
            'mode': 'extractive'
        })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'summary' in data
    assert 'word_count' in data
    assert 'compression_ratio' in data
    assert 'sentiment' in data
    assert 'keywords' in data

def test_summarize_url(client, auth_headers):
    response = client.post('/summarize',
        headers=auth_headers,
        json={
            'url': 'https://example.com/article',
            'mode': 'abstractive'
        })
    assert response.status_code == 200
    assert 'summary' in json.loads(response.data)

def test_rate_limiting(client, auth_headers):
    # Make 6 requests in quick succession
    for i in range(6):
        response = client.post('/summarize',
            headers=auth_headers,
            json={
                'text': 'Test text',
                'mode': 'extractive'
            })
        if i < 5:
            assert response.status_code == 200
        else:
            assert response.status_code == 429  # Too Many Requests

def test_invalid_input(client, auth_headers):
    response = client.post('/summarize',
        headers=auth_headers,
        json={
            'invalid_key': 'some text',
            'mode': 'extractive'
        })
    assert response.status_code == 422

def test_unauthorized_access(client):
    response = client.post('/summarize',
        json={
            'text': 'Test text',
            'mode': 'extractive'
        })
    assert response.status_code == 401  # Unauthorized