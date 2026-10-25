# -*- coding: utf-8 -*-
"""Execute every query in 03_queries.sql, write one CSV per query."""
import re
import os
import csv
import time
import json
import pymysql

SRC = r"D:\桌面\数据库大作业\DOTE6751_LinkedIn\sql\03_queries.sql"
OUT = r"D:\桌面\数据库大作业\DOTE6751_LinkedIn\query_results"
os.makedirs(OUT, exist_ok=True)

text = open(SRC, encoding="utf-8").read()
marker = re.compile(r"^-- @query (Q\d+) \| (.+)$", re.M)
matches = list(marker.finditer(text))
print("queries found:", len(matches))

conn = pymysql.connect(host="127.0.0.1", user="root", password="zsy20040609",
                       charset="utf8mb4", database="linkedin_db", autocommit=True,
                       cursorclass=pymysql.cursors.DictCursor)
summary = []
for i, m in enumerate(matches):
    qid, title = m.group(1), m.group(2).strip()
    start = m.end()
    end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
    body = text[start:end]
    # drop trailing section banners / footer comments
    body = re.split(r"^-- ####", body, flags=re.M)[0]
    body = body.strip().rstrip(";").strip()
    t0 = time.time()
    try:
        with conn.cursor() as cur:
            cur.execute(body)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description] if cur.description else []
        ms = round((time.time() - t0) * 1000)
        path = os.path.join(OUT, f"{qid.lower()}_result.csv")
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for r in rows:
                w.writerow(r)
        summary.append(dict(q=qid, title=title, rows=len(rows), ms=ms, cols=cols))
        print(f"{qid}: {len(rows):4d} rows  {ms:5d} ms  cols={len(cols)}")
    except Exception as e:
        print(f"{qid}: ERROR {e}")
        summary.append(dict(q=qid, title=title, error=str(e)))

json.dump(summary, open(os.path.join(OUT, "_summary.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("\nfailures:", sum(1 for s in summary if "error" in s))
