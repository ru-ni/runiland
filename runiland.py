from flask import Flask, jsonify, render_template, request
import random
import math
from tinydb import *
from flask_socketio import SocketIO


app = Flask(__name__)
sb = TinyDB('shout.json')
nb = TinyDB('news.json')

socketio = SocketIO(app)

PageSize = 50

def bookmark():
#bookmark is the cur page they'll write to
    return list(sorted(sb.tables()))[len(sorted(sb.tables()))-2]#-2 because the last element is always _default

def getpage():
#return contents of cur page
    return sb.table(bookmark()).all()

def checkpage():
#return true or false if it's full or not
    return len(getpage()) < PageSize

def addshout(author,message):
    sb.table(bookmark()).insert({'by': author, 'shout': message})

def addpage(author,message):#here we inaugurate a new page with a post
    if bookmark() == '_default':
        sb.table('1').insert({'by': author, 'shout': message})
    else:
        sb.table(str(int(bookmark())+1)).insert({'by': author, 'shout': message})
        
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
    """
    This is where we wanna expand things
    
    Currently we're just throwing data into the database and then dumping it back out
    ideally, i'd like for the db to be sorted into pages
    
    For testing; 5 posts per page and new pages are created when needed
    Tinydb has sequential id's for its elements and we'll use those as our bookmark.
    We'll add posts to wherever the bookmark currently is.
    
    If there are already LIMIT number of posts on that page then it will
    create a new page and post the shout there instead
    
    
    everything toplevel in a tinydb db.insert() is treated like a table?
    
    newpage = sb.table(str(len(sb.tables())))
    ^creates a new page +1'd of current
    
    
    
    """
    if author+message!='test':
        if checkpage():
            addshout(author,message)
        else:
            addpage(author,message)
        
    
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
    nb.insert({"title":title, "body":body, "by":by})
    
@socketio.on('modpost')
def wsmodpost(json):
    ind = json["data"]["ind"]
    ind = int(ind)
    title = json["data"]["a"]
    body = json["data"]["b"]
    by = json["data"]["c"]
    nb.update({"title":title, "body":body, "by":by}, doc_ids=[ind])
    print('received: {} {} {} {}'.format(title,body,by,ind))
    
@socketio.on('getpage')
def wsgetpage(json):
    #print()
    socketio.emit('my_response', {"list":getpage(), "pages":len(sb.tables())}) 
@socketio.on('addshout')
def wsaddshout(json):
    return shout(json["author"],json["message"])

if __name__ == '__main__':
    socketio.run(app)