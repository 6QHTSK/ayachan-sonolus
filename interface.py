import os
import time
import math
import urllib.parse

import requests

search = {
    "options": [
        {
            "query": "query",
            "name": "搜索",
            "type": "text",
            "placeholder": "可按谱师、标题、正文内容搜索 by 彩绫与6QHTSK"
        },
        {
            "query": "level_min",
            "name": "最低等级",
            "type": "slider",
            "def": 5,
            "min": 5,
            "max": 30,
            "step": 1,
            "display": "number"
        },
        {
            "query": "level_max",
            "name": "最高等级",
            "type": "slider",
            "def": 30,
            "min": 5,
            "max": 30,
            "step": 1,
            "display": "number"
        },
        {
            "query": "time",
            "name": "谱面长度",
            "type": "select",
            "def": 0,
            "values": ['不限', '短版 (<180s)', '长版/FULL (180-420s)', '巨长版/串烧 (>420s)']
        },
        {
            "query": "nps",
            "name": "谱面密度（平均NPS)",
            "type": "select",
            "def": 0,
            "values": ['不限', '一般 (<11note/s)', '密集 (>11note/s)']
        },
        {
            "query": "sp_rhythm",
            "name": "是否含SP音符",
            "type": "select",
            "def": 0,
            "values": ["不限", "含SP音符", "不含SP音符"]
        },
        {
            "query": "regular",
            "name": "[BETA] 谱面风格（是否含换手/多压）",
            "type": "select",
            "def": 0,
            "values": ["不限", "传统（不含换手/多压）", "创新（含换手/多压）"]
        },
    ]
}

ayachanAPI = os.getenv('ayachan_api')
bestdoriAPI = os.getenv('bestdori_api')
diffStr = {0: '[EZ]', 1: '[NM]', 2: '[HD]', 3: '[EX]', 4: '[SP]'}
engineLastUpdate = 0
engine = {}


def convert_sonolus(doc):
    pre_str = '[SP键]' if doc["sp_rhythm"] else ''
    minute = math.floor(doc["total_time"] / 60.0)
    sec = doc["total_time"] - minute * 60.0
    sono_doc = {
        "name": doc["id"],
        "version": 1,
        "rating": doc["level"],
        "title": doc["title"] + diffStr.get(doc["diff"], "[??]"),
        "artists": doc["artists"],
        "author": "%s %s@%s [%.0f:%02.0f, %d note, %.1f nps]" % (
            pre_str, doc["author"]["nickname"], doc["author"]["username"], minute, sec, doc["total_note"],
            doc["total_nps"]),
        "cover": {"type": "LevelCover",
                  "url": doc["song_url"]["cover"].replace('https://bestdori.com',
                                                          "https://jp.bestdori.sonolus.cn")},
        "bgm": {"type": "LevelBgm",
                "url": doc["song_url"]["audio"].replace('https://bestdori.com',
                                                        "https://jp.bestdori.sonolus.cn")},
        "data": {"type": "LevelData",
                 "url": "https://servers.sonolus.cn/bestdori/levels/%d/data?0.6.5" % doc["id"]}
    }
    sono_doc.update(get_engine())
    return sono_doc, doc["content"]


def get_engine():
    global engine, engineLastUpdate
    if int(time.time()) - engineLastUpdate > 3600:
        url = urllib.parse.urljoin(bestdoriAPI, 'engine')
        engine_req = requests.get(url).json()
        if engine_req["result"]:
            engine = engine_req["engine"]
            engineLastUpdate = int(time.time())
    return engine


def search_core(parm):
    url = urllib.parse.urljoin(ayachanAPI, 'v2/bestdori/list')
    req = requests.PreparedRequest()
    req.prepare_url(url, parm)

    return requests.get(req.url).json()


def get_chart_list(page=0, query="", level_min=5, level_max=30, chart_time=0, nps=0, sp_rhythm=0, regular=0):
    parm = {
        "page": page,
        "query": query,
        "level_min": level_min,
        "level_max": level_max,
        "sp_rhythm": sp_rhythm,
        "regular": regular,
    }
    if chart_time == 1:
        parm["time_min"] = 0
        parm["time_max_en"] = 1
        parm["time_max"] = 180
    elif chart_time == 2:
        parm["time_min"] = 180
        parm["time_max_en"] = 1
        parm["time_max"] = 420
    elif chart_time == 3:
        parm["time_min"] = 420
        parm["time_max_en"] = 0

    if nps == 1:
        parm["nps_min"] = 0
        parm["nps_max_en"] = 1
        parm["nps_max"] = 11
    elif nps == 2:
        parm["nps_min"] = 11
        parm["nps_max_en"] = 0

    docs = search_core(parm)

    if docs["result"]:
        sono_docs = []
        for doc in docs["docs"]:
            sono_doc, _ = convert_sonolus(doc)
            sono_docs.append(sono_doc)
        return {
            "pageCount": docs["totalPage"],
            "items": sono_docs,
            "search": search,
        }

    return {
        "pageCount": 0,
        "items": [],
        "search": search,
    }


def get_chart(chart_id):
    url = urllib.parse.urljoin(ayachanAPI, 'v2/bestdori/list/%d' % chart_id)
    doc_req = requests.get(url).json()
    if doc_req["result"]:
        parm = {
            "limit": 6,
            "query": "%s %s %s" % (doc_req["doc"]["title"], doc_req["doc"]["artists"], doc_req["doc"]["author"]["username"])
        }
        doc, des = convert_sonolus(doc_req["doc"])
        recommended_docs = search_core(parm)
        recommended = []
        if recommended_docs["result"]:
            for recommended_doc in recommended_docs["docs"]:
                if recommended_doc["id"] == doc["name"]:
                    continue
                if len(recommended) >= 5:
                    break
                sono_doc, _ = convert_sonolus(recommended_doc)
                recommended.append(sono_doc)

        return {
            "item": doc,
            "description": des,
            "recommended": recommended
        }
    return {}
