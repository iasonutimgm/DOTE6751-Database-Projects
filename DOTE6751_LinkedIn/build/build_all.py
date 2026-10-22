# -*- coding: utf-8 -*-
"""One-command rebuild: schema -> seed -> views/triggers -> queries -> audit.

The MySQL client refuses a non-ASCII path, so the three loadable scripts are
copied to a scratch directory before `source` is called.
"""
import os
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PY = sys.executable
MYSQL = r"E:\mysql\MySQL Server 8.0\bin\mysql.exe"
DELIV = r"D:\桌面\数据库大作业\LinkedIn_交付"
WORK = os.path.dirname(os.path.abspath(__file__))   # build/ ships every generator
TMP = r"C:\Windows\Temp\li_sql"
PASSWORD = "zsy20040609"

os.makedirs(TMP, exist_ok=True)


def run(cmd, **kw):
    print("+", " ".join(cmd) if isinstance(cmd, list) else cmd)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", **kw)
    if r.stdout.strip():
        print(r.stdout.strip())
    if r.returncode != 0:
        print("STDERR:", r.stderr.strip()[:2000])
        raise SystemExit(f"failed: {cmd}")


def mysql_source(name):
    shutil.copyfile(os.path.join(DELIV, "sql", name), os.path.join(TMP, name))
    env = dict(os.environ, MYSQL_PWD=PASSWORD)
    run([MYSQL, "-uroot", "--default-character-set=utf8mb4",
         f"--execute=source {TMP.replace(chr(92), '/')}/{name}"], env=env)


run([PY, os.path.join(WORK, "gen_seed.py")], cwd=WORK)
mysql_source("01_schema.sql")
mysql_source("02_seed.sql")
mysql_source("04_views_triggers.sql")
run([PY, os.path.join(WORK, "build_queries.py")], cwd=WORK)
run([PY, os.path.join(WORK, "run_queries.py")], cwd=WORK)
run([PY, os.path.join(WORK, "verify_data.py")], cwd=WORK)

env = dict(os.environ, MYSQL_PWD=PASSWORD)
for check in [
    "SELECT COUNT(*) FROM linkedin_db.application",
    "SELECT COUNT(*) FROM linkedin_db.interview",
]:
    run([MYSQL, "-uroot", "--default-character-set=utf8mb4", "--execute=" + check], env=env)
print("\nrebuild complete")
