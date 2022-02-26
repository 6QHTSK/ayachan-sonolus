import urllib.parse

import flask
import requests
from flask import Flask, request

import interface

app = Flask(__name__)


@app.route("/bestdori/info")
def info():
    levels = interface.get_chart_list()
    levels["items"] = levels["items"][:5]
    return {
        "levels": levels,
        "skins": {},
        "backgrounds": {},
        "effects": {},
        "particles": {},
        "engines": {}
    }


@app.route("/bestdori/levels/list")
def list():
    parm = {
        "page": request.args.get("page", 0, int),
        "query": request.args.get("query", ""),
        "level_min": request.args.get("level_min", 5, int),
        "level_max": request.args.get("level_max", 30, int),
        "sp_rhythm": request.args.get("sp_rhythm", 0, int),
        "regular": request.args.get("regular", 0, int),
        "chart_time": request.args.get("time", 0, int),
        "nps": request.args.get("nps", 0, int)
    }
    return interface.get_chart_list(**parm)


@app.route("/bestdori/levels/<int:chart_id>")
def chart(chart_id):
    return interface.get_chart(chart_id)


@app.route("/<path:redirect_url>")
def redirect(redirect_url):
    query_dict = request.args.to_dict()
    url = urllib.parse.urljoin("https://servers.sonolus.cn/bestdori", redirect_url)
    req = requests.PreparedRequest()
    req.prepare_url(url, query_dict)
    loc = req.url
    return flask.redirect(loc, code=302)


if __name__ == "__main__":
    app.run('0.0.0.0', port=9000)
