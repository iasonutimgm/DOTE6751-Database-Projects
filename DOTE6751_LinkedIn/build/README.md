# build/ — how the deliverables were generated

Everything in this folder is a build script, not a deliverable. The deliverables are the
SQL scripts, the diagrams, the documents and the results; these scripts exist so that a
reader can regenerate them instead of trusting them.

| Script | Produces |
|---|---|
| `gen_seed.py` | `sql/02_seed.sql` — the deterministic instance (seed 20261115) |
| `build_queries.py` | `sql/03_queries.sql` from `queries_template.sql`, choosing the Q09 member and Q18 posting from the loaded data |
| `run_queries.py` | `query_results/q01…q18_result.csv` + `_summary.json` |
| `verify_data.py` | `query_results/_consistency_report.json` — the 22 invariants |
| `fault_injection.py` | 14 refused statements, quoted in `design/Constraint_Inventory.md` §4 |
| `erd.py` | `erd/*.png` and `*.svg` — logical, conceptual and three modules |
| `gen_normalization_xlsx.py` | `design/Normalization_Proof.xlsx` — 16 sheets |
| `build_deck.py` | `slides/LinkedIn.pptx` — 14 slides with notes |
| `build_narrative_docx.py` | `slides/LinkedIn_Narrative.docx` |
| `build_file_guide.py` | `File_Guide.docx` by scanning the delivered tree |

## Running them

```powershell
python build_all.py        # seed -> schema -> views/triggers -> queries -> audit
```

`build_all.py` is the only entry point needed for a rebuild. It calls the other scripts in
dependency order and prints the row counts and the audit summary.

## One caveat

The scripts carry absolute paths to the delivery folder and to the MySQL client on this
machine:

```python
MYSQL  = r"E:\mysql\MySQL Server 8.0\bin\mysql.exe"
DELIV  = r"D:\桌面\数据库大作业\LinkedIn_交付"
```

If the folder is moved, edit those two constants at the top of `build_all.py` (and the
`OUT` / `DELIV` constants at the top of the individual scripts). They were left absolute
rather than made relative because the MySQL client on Windows refuses to open a `source`
file whose path contains non-ASCII characters, so the build copies each script to an ASCII
scratch directory first; that copy step needs a concrete source path.

The database itself does not depend on any of this: `sql/01_schema.sql`, `02_seed.sql`,
`04_views_triggers.sql` and `03_queries.sql` are plain SQL and run anywhere.
