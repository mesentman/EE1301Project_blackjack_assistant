from flask import Flask, render_template


APP = Flask(__name__)
PORT = 5500
external_ip = ""


@APP.route("/")
def home():
    return render_template("index.html", ip=external_ip)


def run_server(ip: str):
    global external_ip
    external_ip = ip.removeprefix("https://")
    APP.run(port=PORT, debug=False)
