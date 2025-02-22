from flask import Flask,render_template,url_for,request,redirect,session
from werkzeug.security import generate_password_hash,check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO,emit


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.secret_key= "my_secret_key"

db = SQLAlchemy(app)
socketio = SocketIO(app)

class User(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(15),unique=True,nullable=False)
    password = db.Column(db.String(120),nullable=False)

    def set_password(self,password):
        self.password = generate_password_hash(password) 

    def check_password(self,password):
        return check_password_hash(self.password,password)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())


@socketio.on("send_message")
def handle_message(data):
    username = data['username']
    message = data['message']

    new_message = Message(username=username,message=message)
    db.session.add(new_message)
    db.session.commit()

    print(f"🔹 New message from {username}: {message}")
    emit('receive_message',{"username":username,"message":message},broadcast=True)

#Login Page Route
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('home'))
        else:
            return render_template("login.html",error="Invalid username or password")

    return render_template('login.html')   

#Sign-up Page Route
@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        username = request.form['username']
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user:
            return render_template("signup.html",error="Username already exists!")
    
        #Create a new user
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id
        return redirect(url_for("home"))
    
    return render_template("signup.html")

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("home.html")

@app.route('/logout')
def logout():
    session.pop("user_id",None)
    return redirect(url_for('login'))

@app.route('/chat')
def chat():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user = User.query.get(session["user_id"])
    messages = Message.query.order_by(Message.timestamp).limit(50).all()

    chat_history = [{"username":msg.username,"message":msg.message} for msg in messages]
    return render_template('chat.html',username=user.username, chat_history=chat_history)



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app,debug=True)