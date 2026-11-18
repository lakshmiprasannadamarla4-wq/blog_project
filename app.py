from flask import Flask, render_template, request, jsonify, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'blog123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(80), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, nullable=False)
    author = db.Column(db.String(80), nullable=False)
    text = db.Column(db.Text, nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

# RESTful APIs
@app.route('/api/register', methods=['POST'])
def register():
    d = request.json
    if User.query.filter_by(username=d['username']).first():
        return jsonify({'error': 'User exists'}), 400
    u = User(username=d['username'], password=generate_password_hash(d['password']))
    db.session.add(u); db.session.commit()
    return jsonify({'message': 'Registered'})

@app.route('/api/login', methods=['POST'])
def login():
    d = request.json
    u = User.query.filter_by(username=d['username']).first()
    if u and check_password_hash(u.password, d['password']):
        session['user'] = u.username
        return jsonify({'message': 'Login success', 'user': u.username})
    return jsonify({'error': 'Invalid'}), 401

@app.route('/api/posts', methods=['GET', 'POST'])
def posts():
    if request.method == 'GET':
        all_posts = Post.query.all()
        result = []
        for p in all_posts:
            comments = Comment.query.filter_by(post_id=p.id).all()
            result.append({'id': p.id, 'title': p.title, 'content': p.content, 'author': p.author,
                           'comments': [{'author': c.author, 'text': c.text} for c in comments]})
        return jsonify(result)
    d = request.json
    p = Post(title=d['title'], content=d['content'], author=session.get('user', 'Guest'))
    db.session.add(p); db.session.commit()
    return jsonify({'message': 'Post created'})

@app.route('/api/posts/<int:id>', methods=['PUT', 'DELETE'])
def post_one(id):
    p = Post.query.get(id)
    if request.method == 'DELETE':
        Comment.query.filter_by(post_id=id).delete()
        db.session.delete(p); db.session.commit()
        return jsonify({'message': 'Deleted'})
    d = request.json
    p.title = d['title']; p.content = d['content']
    db.session.commit()
    return jsonify({'message': 'Updated'})

@app.route('/api/comment', methods=['POST'])
def comment():
    d = request.json
    c = Comment(post_id=d['post_id'], author=session.get('user', 'Guest'), text=d['text'])
    db.session.add(c); db.session.commit()
    return jsonify({'message': 'Comment added'})

if __name__ == '__main__':
    app.run(debug=True)
