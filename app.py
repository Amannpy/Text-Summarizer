from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import os
from newspaper import Article
from pdfminer.high_level import extract_text
from docx import Document
from transformers import pipeline
from textblob import TextBlob
from models import User, Summary, db

def extract_text_from_pdf(file):
    return extract_text(file)

def extract_text_from_docx(file):
    doc = Document(file)
    return '\n'.join([para.text for para in doc.paragraphs])

# Initialize the summarization pipeline with the facebook/bart-large-cnn model
summarizer = pipeline('summarization', model='facebook/bart-large-cnn')

def abstractive_summarize(text):
    return summarizer(text, max_length=150, min_length=30, do_sample=False)[0]['summary_text']

def extractive_summarize(text):
    from gensim.summarization import summarize
    try:
        clean_text = ' '.join(text.split())
        summary = summarize(clean_text, ratio=0.2, split=True)
        return ' '.join(summary).replace(' .', '.').strip()
    except ValueError:
        sentences = text.split('. ')
        return '. '.join(sentences[:3]) + '.'

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

db.init_app(app)

jwt = JWTManager(app)
limiter = Limiter(app=app, key_func=get_remote_address)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password') or not data.get('email'):
        return jsonify({'error': 'Missing required fields'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400

    user = User(username=data['username'], email=data['email'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing username or password'}), 400

    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify({'access_token': access_token}), 200

    return jsonify({'error': 'Invalid username or password'}), 401

@app.cli.command('init-db')
def init_db():
    db.create_all()
    print('Database initialized successfully')

@app.route('/summarize', methods=['POST'])
@jwt_required()
@limiter.limit("5 per minute")
def summarize():
    data = request.get_json()
    text = data.get('text')
    file = request.files.get('file')
    url = data.get('url')
    mode = data.get('mode', 'abstractive')
    
    if url:
        article = Article(url)
        article.download()
        article.parse()
        text = article.text
    elif file:
        if file.filename.endswith('.pdf'):
            text = extract_text_from_pdf(file)
        elif file.filename.endswith('.docx'):
            text = extract_text_from_docx(file)
        
    if not text:
        return jsonify({'error': 'No valid input provided'}), 400
    
    if mode == 'abstractive':
        summary = abstractive_summarize(text)
    elif mode == 'extractive':
        summary = extractive_summarize(text)
    
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity
    
    keywords = [word for word, pos in blob.tags if pos.startswith('NN')][:5]
    
    user_id = get_jwt_identity()
    summary_record = Summary(
        content=text,
        summary=summary,
        user_id=user_id,
        mode=mode
    )
    db.session.add(summary_record)
    db.session.commit()
    
    return jsonify({
        'summary': summary,
        'word_count': len(summary.split()),
        'compression_ratio': len(summary)/len(text),
        'sentiment': sentiment,
        'keywords': keywords
    })

if __name__ == '__main__':
    app.run(debug=True)