from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from flask import Flask, Response, redirect, url_for, request, session, abort
from flask import Flask, jsonify, render_template, request
import random
import math
from tinydb import *

from flask_socketio import SocketIO
from flask_login import LoginManager, UserMixin, login_required
from itsdangerous import JSONWebSignatureSerializer

import logging
logging.basicConfig(filename='error.log',level=logging.DEBUG)

app = Flask(__name__)
sb = TinyDB('shout.json')
nb = TinyDB('news.json')
db = TinyDB('users.json')

socketio = SocketIO(app)

# flask-login
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

def getpage():
#return contents of cur page
    return sb.all()

      
def collatz(num):
    cur = num
    output = []
    output.append(num)
    while cur > 0:
        if cur % 2 == 1:
            cur = cur * 3 + 1
            output.append(int(cur))
        else:
            cur = cur / 2
            output.append(int(cur))
        if cur == 1:
            return output

def shout(author,message):
    sb.insert({'by': author, 'shout': message})
    return getpage()

@app.route('/_add_shout')
def add_numbers():
    a = request.args.get('a', '', type=str)
    b = request.args.get('b', '', type=str)
    return jsonify(result=shout(a,b))
@app.route('/_get_shouts')
def get_shouts():
    return jsonify(result=shout("te","st"))

@app.route('/')
def root():
    tab = nb.table('_default').all()
    posts = []
    ind = 1
    for pre in tab:
        posts.append({"body":pre["body"],
        "title":pre["title"],
        "by":pre["by"],
        "ind":ind})
    send = {"sidebar":{},
            "posts":posts}
    return render_template('news.html', data=send)

@app.route('/news/')
@login_required
def newsroom():
    tab = nb.table('_default').all()
    posts = []
    ind = 1
    for pre in tab:
        posts.append({"body":pre["body"],
            "title":pre["title"],
            "by":pre["by"],
            "ind":ind})
        ind+=1
    return render_template('editnews.html', data=posts)

@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)

@app.route('/backtrace/')
def backtrace():
    return render_template('backtrace.html')

@app.route('/quest/')
@app.route('/quest/<id>')
def quest(id=None):
    return render_template('quest.html', id=id)

@app.route('/collatz/')
@app.route('/collatz/<num>')
def colcalc(num=None):
    if num:
        coltable = collatz(int(num))
        peak = 0
        for val in coltable:
            if val > peak:
                peak = val
        verbose = []
        for val in coltable:
            curcol = collatz(int(val))
            deeppeak = 0
            for v in curcol:
                if v > deeppeak:
                    deeppeak = v
            verbose.append('{} | Chain length: {}, Peak in chain: {}, Average: {}, Total: {}'.format(val,len(curcol),
                                                                                                     deeppeak,math.floor(sum(curcol)/len(curcol)),
                                                                                                     sum(curcol)))
        data = {'brief':'Chain length: {}, Peak in chain: {}, Average: {}'.format(len(coltable),peak,math.floor(sum(coltable)/len(coltable))),'nums':verbose}
    else:
        rand = random.randint(0,69420)
        coltable = collatz(int(rand))
        peak = 0
        for val in coltable:
            if val > peak:
                peak = val
        verbose = []
        for val in coltable:
            curcol = collatz(int(val))
            deeppeak = 0
            for v in curcol:
                if v > deeppeak:
                    deeppeak = v
            verbose.append('{} | Chain length: {}, Peak in chain: {}, Average: {}, Total: {}'.format(val,len(curcol),
                                                                                                     deeppeak,math.floor(sum(curcol)/len(curcol)),
                                                                                                     sum(curcol)))
        data = {'brief':'Chain length: {}, Peak in chain: {}, Average: {}'.format(len(coltable),peak,math.floor(sum(coltable)/len(coltable))),'nums':verbose}
    return render_template('collatz.html', data=data)

@socketio.on('message')
def handle_message(message):
    print('received message: ' + message)
    
@socketio.on('json')
def handle_json(json):
    print('received json: ' + str(json))
    
@socketio.on('my event')
def handle_my_custom_event(json):
    print('received: ' + str(json))

@socketio.on('addpost')
def wsaddpost(json):
    title = json["data"]["a"]
    body = json["data"]["b"]
    by = json["data"]["c"]
    if title and body and by != "":
        ind = nb.insert({"title":title, "body":body, "by":by})
        nb.update({"title":title, "body":body, "by":by, "ind":ind}, doc_ids=[ind])
    
@socketio.on('modpost')
def wsmodpost(json):
    ind = json["data"]["ind"]
    ind = int(ind)
    title = json["data"]["a"]
    body = json["data"]["b"]
    by = json["data"]["c"]
    if title == "" or body == "" or by == "":
        if title == "" and body == "" and by == "":
            nb.remove(doc_ids=[ind])
    else:
        nb.update({"title":title, "body":body, "by":by}, doc_ids=[ind])
    
    tab = nb.table('_default').all()
    posts = []
    ind = 1
    for pre in tab:
        posts.append({"body":pre["body"],
            "title":pre["title"],
            "by":pre["by"],
            "ind":ind})
        ind+=1
    socketio.emit('getnewsresp', {"list":posts}) 

@socketio.on('getnews')
def wsgetnews(json):
    tab = nb.table('_default').all()
    #posts = []
    #ind = 1
    #for pre in tab:
        #posts.append({"body":pre["body"],
            #"title":pre["title"],
            #"by":pre["by"],
            #"ind":ind})
        #ind+=1
    socketio.emit('getnewsresp', {"list":tab}) 
    
@socketio.on('getpage')
def wsgetpage(json):
    #print()
    socketio.emit('getpageresp', {"list":getpage(), "pages":len(sb.tables())}) 
    
@socketio.on('addshout')
def wsaddshout(json):
    return shout(json["author"],json["message"])

class User(UserMixin):
    # proxy for a database of users

    def __init__(self, id, username, hash):
        self.id = id
        self.username = username
        self.hash = hash

    @classmethod
    def get(cls,id):
        try:
            return db.search(where('id') == id)[0] 
        except:
            return None

@login_manager.request_loader
def load_user(request):
    token = request.headers.get('Authorization')
    if token is None:
        token = request.args.get('token')

    if token is not None:
        id= token.split(":")[0]
        password = token.replace(id+":","")
        user_entry = User.get(id)
        #returns {"id":str,"username":str,"hash":str}
        if (user_entry is not None):
            user = User(user_entry["id"],user_entry["username"],user_entry["hash"])
            #print(id,password,user_entry)
            if (check_password_hash(user.hash, password)):
                print(user.hash,password)
                return user
    return None

@app.route("/protected/",methods=["GET", "POST"])
#@login_required
def protected():
    #return generate_password_hash('Hello')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']#generate_password_hash()
        print(username,password)
        
        u = User.get(username)
        if u:# == username + "_secret":
            user = User(u["id"],u["username"],u["hash"])
            if check_password_hash(u["hash"], password):
                if login_user(user):
                    print(username,password)
                    
                return redirect("/news")
            else:
                return abort(401)
        else:
            return abort(401)
    else:
        return Response('''
        <form action="" method="post">
            <p><input type=text name=username>
            <p><input type=password name=password>
            <p><input type=submit value=Login>
        </form>
        ''')


if __name__ == '__main__':
    #import logging
    #logging.basicConfig(filename='error.log',level=logging.DEBUG)
    socketio.run(app)