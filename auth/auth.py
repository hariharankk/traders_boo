from flask import Flask, request, session, jsonify, url_for,render_template
from flask_sqlalchemy import SQLAlchemy
from flask_ngrok import run_with_ngrok
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_required, logout_user, login_user,UserMixin
import jwt
from flask_mail import Message, Mail
from time import time
from config import Config


app = Flask(__name__)

app.config.from_object(Config)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
mail = Mail(app)


class User(db.Model,UserMixin):
    """ Create user table"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(80), unique=True)
    password_hash = db.Column(db.String(128))
    email_verified = db.Column(db.String(80))
   
    @property
    def password(self):
        raise AttributeError('password is not a readable property')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


    @staticmethod
    def validate_email(email):
        if User.query.filter_by(email = email).first() is not None:
            return False
        else:
            return True
  
    def validate_email_verification(self):
      if self.email_verified == 'user verified':
        return True
      else:
        return False  
  
    @staticmethod
    def validate_username(field):
        if User.query.filter_by(username=field).first() is not None:
            return False
        else:
            return True
    
    @staticmethod
    def verify_email(email):
      user = User.query.filter_by(email = email).first()
      return user
    
    @staticmethod
    def get_reset_password_token(id, expires_in=600):
        return jwt.encode(
            {'reset_password': id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256'
        )

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'], algorithm=['HS256']) ['reset_password']
        except:
            return

        return id 
    
    def __repr__(self):
        return '<User {}>'.format(self.email)  


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login Form"""
    if request.method == 'POST':
        #remember = request.form['remember']
        try:      
         user = User.query.filter_by(email=request.form['email']).first()
         if user is not None and user.check_password(request.form['password']) and user.validate_email_verification() :         
                login_user(user , remember = request.form['remember'])
                session['mail'] = request.form['email']
                token = User.get_reset_password_token(user.id)
                send_email(
                  'confirm login',
                   sender = app.config['ADMINS'][0],
                   recipients = [user.email],
                   text_body = f'''hello {user.username} ,
                    good to have you at traders'boon. 
                    To confirm your login , visit on following link: {url_for('validate_login', token=token, _external=True)} 
                    If you did not make this request just ignore this mail.''',
                )
                return jsonify({'status':'Login done'})
         else:
                return jsonify({'status':'you have logged in properly'})
        except:
            return jsonify({'status':'hari, you are not a good developer'})
    else:
      return jsonify({'status':'get the right kind of request'})


@app.route('/validate_login/<token>',methods=["GET"])   
def validate_login(token):  
   if session.get('mail'):
        return {"status": "user is logged in, so can't reset password"}

   id = User.verify_reset_password_token(token)
   user = User.query.get(id)

   if not user:
       return {"status": "can't find user"}
   else:  
       return "<h3> Your email has been successfully verified! </h3>"  


@app.route('/register/', methods=['GET', 'POST'])
def register():
    """Register Form"""
    if request.method == 'POST':
      value_email = User.validate_email(request.form['email'])
      value_username = User.validate_username(request.form['username'])
      if value_email and value_username:
          new_user = User(
              email = request.form['email'],
              username = request.form['username'],
              password = request.form['password'],
              email_verified = 'not verified' )
          db.session.add(new_user)
          db.session.commit()
          token = User.get_reset_password_token(request.form['email'])
          send_email(
                   'confirm Registration',
                   sender = app.config['ADMINS'][0],
                   recipients = [request.form['email']],
                   text_body = f'''hello {request.form['username']} , 
                   welcome to traders'boon, we are happy to help you trade better. 
                   To confirm your registration , visit on following link: {url_for('validate_register', token=token, _external=True)} 
                   If you did not make this request just ignore this mail.''',
                )

          return jsonify({'status':'registered and now 2fa'})
      else:
        return jsonify({'status':'enter unique email id'})
      return jsonify({'status':'failed to register'})
    else:
      return jsonify({'status':'Dont register'})

@app.route('/validate_register/<token>',methods=["GET"])   
def validate_register(token):  
   if session.get('mail'):
        return {"status": "user is logged in, so can't reset password"}

   email = User.verify_reset_password_token(token)
   user = User.query.filter_by(email=email).first()
   if not user:
       return {"status": "can't find user"}
   else:  
       user.email_verified = 'user verified'
       db.session.commit()
       return "<h3> Your email has been successfully verified! </h3>"  

@app.route("/logout")
@login_required
def logout():
    if "_user_id" in session:
        session.pop("mail")
    logout_user()
    return jsonify({'status':'logged_out'})


@app.route("/resetpassword",methods=['POST'])
@login_required
def resetpassword():
   if request.method == 'POST':
      if session.get('mail') == request.form['email']:
          
          old_pass, new_pass = request.form["old_pass"], request.form["new_pass"]
          user = User.query.filter_by(email=request.form['email']).first()
          
          # Check if user password does not match with old password.
          if not user.check_password(old_pass):
                # Return does not match status.
              return {"status": "old password does not match."}
          # Update password.
          user.password = new_pass
          # Commit session.
          db.session.commit()

        # Return success status.
      else:
          return {"status": "don't fake asshole."}
      
      return {"status": "password changed."}

@app.route('/api/users/<int:id>')
def get_user(id):
    user =  User.query.get(id)
    if not user:
        return jsonify({'username': 'not found' })
    return jsonify({'username' : user.username , 'email' : user.email })

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def send_email(subject, sender, recipients, text_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    mail.send(msg)

def send_password_reset_email(user):
    token = user.get_reset_password_token()

    send_email(
        'Reset Password',
        sender = app.config['ADMINS'][0],
        recipients = [user.email],
        text_body = f'''To reset your password, visit on following link: {url_for('reset_password', token=token, _external=True)} If you did not make this request just ignore this mail.''',
    )

@app.route('/reset_password_request', methods=['POST'])
def reset_password_request():
    if session.get('mail'):
        return {"status": "user is logged in, so can't reset password"}


    user = User.query.filter_by(email=request.form['email']).first()
    if user:
            send_password_reset_email(user)
            return {"status": "Check your email for the instructions to reset your password."}
    else:
      return {"status": "sorry, register first"}
        


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
   if session.get('mail'):
        return {"status": "user is logged in, so can't reset password"}

   user = User.verify_reset_password_token(token)

   if not user:
       return {"status": "can't find user"}


   form = ResetPasswordForm()

   if form.validate_on_submit():
        user.password = form.password.data
        db.session.commit()
        return {"status": "user password is regitered"}

   return {"status": "form is not valid"}    


if __name__ == '__main__':
    db.create_all()
    app.run()
