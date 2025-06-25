from flask import Flask
from flask import render_template, request, send_file, jsonify
import os
import random
import string

sendmsg = None

app = Flask(__name__)

if os.path.exists(".webhook.secret"):
    secret = open(".webhook.secret", "r").read()
else:
    secret = ''.join(random.sample(string.ascii_letters + string.digits, 32))
    open(".webhook.secret", "w").write(secret)


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/messagelog.json")
def msglog():
    return str(open('messagelog.json', 'r').read())


@app.route("/hans")
def hans():
    return str(open('HanlinQT.html', 'r', encoding="utf-8").read())


@app.route("/picture_caches/<filename>")
def get_picture(filename):
    return send_file(os.path.join("picture_caches", filename))


from flask import Flask, request, jsonify

@app.route(f"/webhook/{secret}", methods=["GET", "POST"])
@app.route(f"/webhook/{secret}/<platform>", methods=["GET", "POST"])
def webhook(platform=None):
    reqdata = request.get_json(silent=True) or request.form or request.args

    message = None

    # 平台格式處理
    if platform is None:
        message = reqdata.get("message")

    elif platform == "discord":
        # Discord 通常是 {"content": "訊息"}
        message = reqdata.get("content")
        if message:
            sendmsg(message)
        if reqdata.get("embeds"):
            embeds = reqdata.get("embeds")
            for embed in embeds:
                message = f'{embed.get("title", "")}\n{embed.get("description", "")}'
                sendmsg(message)
        return jsonify({"success": "OK"}), 204


    elif platform == "slack":
        # Slack 常見格式為 {"event": {"text": "訊息"}}
        if isinstance(reqdata.get("event"), dict):
            message = reqdata["event"].get("text")

    elif platform == "github":
        # GitHub webhook 有多種事件，這裡只是示範 push event
        if reqdata.get("head_commit"):
            message = reqdata["head_commit"].get("message")

    else:
        return jsonify({"error": f"Unknown platform '{platform}'"}), 400

    if not message:
        return jsonify({"error": "Message is empty."}), 400

    # from main import sendmsg
    sendmsg(message)
    return jsonify({"success": "OK"})


def run():
    ssl_keys = ('server.crt', 'server.key')
    app.run(host='0.0.0.0', port=3000)
