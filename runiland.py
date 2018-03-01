from flask import Flask
from flask import render_template
import random
app = Flask(__name__)


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

@app.route('/')
@app.route('/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)

@app.route('/collatz/')
@app.route('/collatz/<num>')
def colcalc(num=None):
    if num:
        coltable = collatz(int(num))
        data = {'brief':'Chain length: {}'.format(len(coltable)),'nums':coltable}
    else:
        rand = random.randint(0,69420)
        coltable = collatz(int(rand))
        data = {'brief':'You\'ve not given me a number so have a random seed..'+str(rand),'nums':coltable}
    return render_template('collatz.html', data=data)