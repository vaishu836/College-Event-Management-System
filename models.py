from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'admin', 'faculty', or 'student'

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Event(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='events')  # This sets up the relationship

    def __repr__(self):
        return f'<Event {self.title} - {self.date}>'

def new_event (title, description, date, creator_id):
    """Function to save a new event with user association."""
    try:
        new_event = Event(title=title, description=description, date=date, creator_id=creator_id)
        db.session.add(new_event)
        db.session.commit()  # Ensure this is successfully reached
        print(f"Event saved: {new_event}")  # Debugging print statement
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        print(f"Error saving event: {e}")  # Log the error
        raise

class Message(db.Model):
    __tablename__ = 'messages'
   
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # ID of the user who sent the message
    content = db.Column(db.Text, nullable=False)  # Message content
    date = db.Column(db.DateTime, nullable=False) # Date and time when the message was sent
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    is_read = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Message {self.id} - From: {self.sender_id} To: {self.recipient_id}>"
