from onu_adress import ip_adress
from flask import Flask, render_template
import json
from save_to_file import MySnmp

app = Flask(__name__)


@app.route("/")
def start():
    sp = []
    with open("result.json", "r") as file:
        info = json.load(file)
        print(info)
    return render_template('index.html', data=info)


app.run(debug=True, host='0.0.0.0', port=5001)

print(start())
