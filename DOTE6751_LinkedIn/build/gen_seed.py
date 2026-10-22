# -*- coding: utf-8 -*-
"""Generate 02_seed.sql for linkedin_db.

Design goal: the data must survive cross-table consistency checks, because
five of the eighteen queries assert relationships between tables (a HIRED
application must have passed interviews, a REFERRAL application must have a
referrer inside the hiring company, hires must not exceed openings, ...).

Everything is deterministic: random.Random(20261115).
"""
import os
import random
import json
from datetime import datetime, timedelta, date

R = random.Random(20261115)
ANCHOR = datetime(2026, 10, 15, 18, 0, 0)      # data snapshot
OUT = r"D:\桌面\数据库大作业\LinkedIn_交付\sql\02_seed.sql"
STATS = r"D:\桌面\数据库大作业\_work_li\seed_stats.json"

CITIES = [("San Francisco", "US"), ("New York", "US"), ("Seattle", "US"), ("Austin", "US"),
          ("London", "GB"), ("Beijing", "CN"), ("Shanghai", "CN"), ("Shenzhen", "CN"),
          ("Singapore", "SG"), ("Tokyo", "JP"), ("Berlin", "DE"), ("Munich", "DE"),
          ("Bangalore", "IN"), ("Toronto", "CA"), ("Sydney", "AU"), ("Seoul", "KR"),
          ("Stockholm", "SE"), ("Taipei", "TW"), ("Dublin", "IE"), ("Helsinki", "FI"),
          ("Zurich", "CH"), ("Copenhagen", "DK"), ("Hong Kong", "HK")]
CITY_BY_COUNTRY = {}
for c, k in CITIES:
    CITY_BY_COUNTRY.setdefault(k, []).append(c)

COMPANIES = [
    ("Google", "Internet", "US", "5001+", 1998, 1),
    ("Microsoft", "Software", "US", "5001+", 1975, 1),
    ("Amazon", "E-commerce", "US", "5001+", 1994, 1),
    ("Meta", "Internet", "US", "5001+", 2004, 1),
    ("Apple", "Consumer Electronics", "US", "5001+", 1976, 1),
    ("Netflix", "Media", "US", "1001-5000", 1997, 1),
    ("Stripe", "Fintech", "US", "1001-5000", 2010, 1),
    ("Airbnb", "Internet", "US", "1001-5000", 2008, 1),
    ("Uber", "Internet", "US", "5001+", 2009, 0),
    ("Shopify", "Software", "CA", "1001-5000", 2006, 1),
    ("Salesforce", "Software", "US", "5001+", 1999, 1),
    ("Adobe", "Software", "US", "5001+", 1982, 1),
    ("Nvidia", "Semiconductors", "US", "5001+", 1993, 1),
    ("Intel", "Semiconductors", "US", "5001+", 1968, 1),
    ("TSMC", "Semiconductors", "TW", "5001+", 1987, 1),
    ("ByteDance", "Internet", "CN", "5001+", 2012, 0),
    ("Tencent", "Internet", "CN", "5001+", 1998, 1),
    ("Alibaba", "E-commerce", "CN", "5001+", 1999, 1),
    ("Grab", "Internet", "SG", "1001-5000", 2012, 0),
    ("Sea Group", "Internet", "SG", "1001-5000", 2009, 1),
    ("Deloitte", "Consulting", "US", "5001+", 1845, 1),
    ("McKinsey", "Consulting", "US", "1001-5000", 1926, 1),
    ("Goldman Sachs", "Banking", "US", "5001+", 1869, 1),
    ("JPMorgan Chase", "Banking", "US", "5001+", 1799, 1),
    ("HSBC", "Banking", "GB", "5001+", 1865, 1),
    ("Samsung Electronics", "Consumer Electronics", "KR", "5001+", 1969, 1),
    ("Sony", "Consumer Electronics", "JP", "5001+", 1946, 1),
    ("Siemens", "Industrial", "DE", "5001+", 1847, 1),
    ("Bosch", "Automotive", "DE", "5001+", 1886, 1),
    ("Infosys", "IT Services", "IN", "5001+", 1981, 1),
    ("Tata Consultancy Services", "IT Services", "IN", "5001+", 1968, 1),
    ("Spotify", "Media", "SE", "1001-5000", 2006, 1),
    ("Snowflake", "Cloud Infrastructure", "US", "1001-5000", 2012, 1),
    ("Databricks", "Cloud Infrastructure", "US", "1001-5000", 2013, 0),
    ("Atlassian", "Software", "AU", "1001-5000", 2002, 1),
    ("Canva", "Software", "AU", "1001-5000", 2013, 0),
    ("Zoom", "Software", "US", "1001-5000", 2011, 0),
    ("Palantir", "Software", "US", "1001-5000", 2003, 1),
    ("SAP", "Software", "DE", "5001+", 1972, 1),
    ("Oracle", "Software", "US", "5001+", 1977, 1),
    ("IBM", "IT Services", "US", "5001+", 1911, 1),
    ("Accenture", "Consulting", "IE", "5001+", 1989, 1),
    ("Shopee", "E-commerce", "SG", "1001-5000", 2015, 0),
    ("Lazada", "E-commerce", "SG", "1001-5000", 2012, 0),
    ("Meituan", "E-commerce", "CN", "5001+", 2010, 1),
    ("JD.com", "E-commerce", "CN", "5001+", 1998, 1),
    ("Baidu", "Internet", "CN", "5001+", 2000, 1),
    ("Xiaomi", "Consumer Electronics", "CN", "5001+", 2010, 1),
    ("Huawei", "Telecom", "CN", "5001+", 1987, 0),
    ("Ericsson", "Telecom", "SE", "5001+", 1876, 1),
    ("Nokia", "Telecom", "FI", "5001+", 1865, 1),
    ("DBS Bank", "Banking", "SG", "5001+", 1968, 1),
    ("OCBC Bank", "Banking", "SG", "5001+", 1932, 1),
    ("CICC", "Banking", "CN", "1001-5000", 1995, 0),
    ("Ping An", "Insurance", "CN", "5001+", 1988, 1),
    ("Allianz", "Insurance", "DE", "5001+", 1890, 1),
    ("AstraZeneca", "Healthcare Tech", "GB", "5001+", 1999, 1),
    ("Roche", "Healthcare Tech", "CH", "5001+", 1896, 1),
    ("Maersk", "Logistics", "DK", "5001+", 1904, 1),
    ("edX", "Education Tech", "US", "201-500", 2012, 0),
]

SKILLS = [
    ("Python", "LANGUAGE", 0), ("Java", "LANGUAGE", 0), ("JavaScript", "LANGUAGE", 0),
    ("TypeScript", "LANGUAGE", 0), ("Go", "LANGUAGE", 0), ("C++", "LANGUAGE", 0),
    ("C#", "LANGUAGE", 0), ("Rust", "LANGUAGE", 1), ("SQL", "LANGUAGE", 0),
    ("R", "LANGUAGE", 0), ("Scala", "LANGUAGE", 0), ("Kotlin", "LANGUAGE", 0),
    ("Swift", "LANGUAGE", 0), ("Ruby", "LANGUAGE", 0),
    ("React", "FRAMEWORK", 0), ("Vue.js", "FRAMEWORK", 0), ("Django", "FRAMEWORK", 0),
    ("Spring Boot", "FRAMEWORK", 0), ("FastAPI", "FRAMEWORK", 0), ("Node.js", "FRAMEWORK", 0),
    (".NET", "FRAMEWORK", 0), ("TensorFlow", "FRAMEWORK", 0), ("PyTorch", "FRAMEWORK", 1),
    ("Kubernetes", "FRAMEWORK", 0), ("Terraform", "FRAMEWORK", 1), ("Spark", "FRAMEWORK", 0),
    ("GraphQL", "FRAMEWORK", 1),
    ("MySQL", "DATABASE", 0), ("PostgreSQL", "DATABASE", 0), ("MongoDB", "DATABASE", 0),
    ("Redis", "DATABASE", 0), ("Snowflake", "DATABASE", 0), ("BigQuery", "DATABASE", 0),
    ("Oracle Database", "DATABASE", 0), ("Elasticsearch", "DATABASE", 0),
    ("AWS", "CLOUD", 0), ("Azure", "CLOUD", 0), ("Google Cloud", "CLOUD", 0),
    ("Alibaba Cloud", "CLOUD", 0),
    ("Data Modelling", "DATA", 0), ("ETL Pipelines", "DATA", 0), ("Airflow", "DATA", 0),
    ("Data Warehousing", "DATA", 0), ("Statistical Analysis", "DATA", 0),
    ("A/B Testing", "DATA", 0), ("Kafka", "DATA", 0), ("dbt", "DATA", 1),
    ("Looker", "DATA", 1),
    ("Product Discovery", "PRODUCT", 0), ("Roadmapping", "PRODUCT", 0),
    ("User Research", "PRODUCT", 0), ("Pricing Strategy", "PRODUCT", 0),
    ("Figma", "DESIGN", 0), ("Interaction Design", "DESIGN", 0), ("Design Systems", "DESIGN", 0),
    ("Stakeholder Management", "SOFT", 0), ("Technical Writing", "SOFT", 0),
    ("Team Leadership", "SOFT", 0), ("Agile Delivery", "SOFT", 0), ("Negotiation", "SOFT", 0),
]

TITLES = {
    "Internet": ["Software Engineer", "Senior Software Engineer", "Data Scientist", "Product Manager",
                 "Product Designer", "Machine Learning Engineer", "Site Reliability Engineer",
                 "Engineering Manager", "Growth Analyst"],
    "Software": ["Backend Engineer", "Frontend Engineer", "Data Engineer", "Product Manager",
                 "Solutions Architect", "Security Engineer", "Engineering Manager",
                 "Technical Program Manager", "QA Engineer"],
    "E-commerce": ["Operations Analyst", "Merchant Manager", "Software Engineer", "Data Analyst",
                   "Logistics Product Manager", "Backend Engineer"],
    "Consulting": ["Consultant", "Senior Consultant", "Engagement Manager", "Data Analyst",
                   "Strategy Analyst", "Digital Transformation Lead"],
    "Banking": ["Analyst", "Associate", "Vice President", "Quantitative Analyst", "Risk Analyst",
                "Technology Auditor"],
    "Semiconductors": ["ASIC Design Engineer", "Verification Engineer", "Process Engineer",
                       "Firmware Engineer", "Data Engineer"],
    "IT Services": ["Systems Engineer", "Cloud Consultant", "Delivery Manager", "Support Engineer",
                    "Data Engineer"],
    "Media": ["Content Strategist", "Streaming Engineer", "Data Analyst", "Recommendation Engineer"],
    "Fintech": ["Payments Engineer", "Risk Analyst", "Backend Engineer", "Compliance Analyst",
                "Data Scientist"],
    "Telecom": ["Network Engineer", "Radio Engineer", "Cloud Engineer", "Data Analyst"],
    "Automotive": ["Embedded Engineer", "Autonomous Systems Engineer", "Supplier Quality Engineer",
                   "Data Engineer"],
    "Healthcare Tech": ["Clinical Data Analyst", "Regulatory Specialist", "Software Engineer",
                        "Data Scientist"],
    "Logistics": ["Operations Manager", "Data Analyst", "Route Optimisation Engineer",
                  "Supply Chain Analyst"],
    "Education Tech": ["Learning Engineer", "Instructional Designer", "Backend Engineer",
                       "Product Manager"],
    "Insurance": ["Actuarial Analyst", "Claims Analyst", "Data Engineer", "Risk Analyst"],
    "Industrial": ["Automation Engineer", "Mechanical Engineer", "Project Manager", "Data Analyst"],
    "Cloud Infrastructure": ["Infrastructure Engineer", "Platform Engineer", "Solutions Architect",
                             "Data Engineer"],
    "Consumer Electronics": ["Hardware Engineer", "Product Manager", "Embedded Engineer",
                             "Data Analyst"],
}

FIRST = ["Wei", "Ming", "Jing", "Hao", "Yan", "Xinyi", "Zhiwei", "Qian", "Rui", "Tao",
         "Priya", "Arjun", "Rahul", "Ananya", "Vikram", "Neha", "Rohan", "Isha", "Karan", "Divya",
         "Emily", "Michael", "Sarah", "Daniel", "Olivia", "James", "Sophia", "Ethan", "Chloe", "Noah",
         "Lucas", "Mia", "Henry", "Grace", "Leo", "Nina", "Oscar", "Ella", "Adam", "Zoe",
         "Haruto", "Yuki", "Sora", "Minjun", "Seoyeon", "Jihoon", "Hana", "Kenji", "Aiko", "Ren",
         "Lars", "Anna", "Felix", "Clara", "Jonas", "Lea", "Matteo", "Sofia", "Elena", "Pablo"]
LAST = ["Zhang", "Wang", "Li", "Chen", "Liu", "Yang", "Huang", "Zhao", "Wu", "Zhou",
        "Xu", "Sun", "Ma", "Zhu", "Hu", "Guo", "He", "Lin", "Gao", "Luo",
        "Sharma", "Patel", "Reddy", "Iyer", "Nair", "Gupta", "Mehta", "Rao", "Khan", "Singh",
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Wilson", "Taylor", "Clark",
        "Anderson", "Thomas", "Moore", "Jackson", "Martin", "Lee", "Walker", "Hall", "Young", "King",
        "Tanaka", "Sato", "Suzuki", "Kim", "Park", "Choi", "Nguyen", "Tran", "Muller", "Schmidt"]

SENIORITY = [("INTERN", 3), ("JUNIOR", 14), ("MID", 30), ("SENIOR", 30), ("LEAD", 15),
             ("PRINCIPAL", 6), ("DIRECTOR", 2)]
SALARY = {"INTERN": (30000, 52000), "JUNIOR": (58000, 95000), "MID": (88000, 135000),
          "SENIOR": (125000, 185000), "LEAD": (165000, 235000),
          "PRINCIPAL": (210000, 300000), "DIRECTOR": (255000, 390000)}

TITLE_SKILLS = [
    ("Machine Learning", ["Python", "TensorFlow", "PyTorch", "Statistical Analysis"]),
    ("Data Scientist", ["Python", "SQL", "Statistical Analysis", "A/B Testing"]),
    ("Data Engineer", ["SQL", "ETL Pipelines", "Airflow", "Spark"]),
    ("Data Analyst", ["SQL", "Looker", "Statistical Analysis", "A/B Testing"]),
    ("Analyst", ["SQL", "Statistical Analysis", "Stakeholder Management"]),
    ("Backend", ["Java", "Python", "PostgreSQL", "Spring Boot"]),
    ("Frontend", ["TypeScript", "React", "Design Systems"]),
    ("Software Engineer", ["Python", "Java", "MySQL", "Kubernetes"]),
    ("Platform", ["Kubernetes", "Terraform", "AWS"]),
    ("Infrastructure", ["Kubernetes", "Terraform", "AWS"]),
    ("Cloud", ["AWS", "Azure", "Terraform"]),
    ("Site Reliability", ["Kubernetes", "Go", "Elasticsearch"]),
    ("Product Manager", ["Product Discovery", "Roadmapping", "A/B Testing"]),
    ("Product Designer", ["Figma", "Interaction Design", "User Research"]),
    ("Designer", ["Figma", "Interaction Design", "Design Systems"]),
    ("QA", ["Python", "Agile Delivery", "Technical Writing"]),
    ("Security", ["Python", "AWS", "Technical Writing"]),
    ("Solutions Architect", ["AWS", "Data Modelling", "Stakeholder Management"]),
    ("Engineering Manager", ["Team Leadership", "Agile Delivery", "Kubernetes"]),
    ("Technical Program", ["Agile Delivery", "Stakeholder Management", "Roadmapping"]),
    ("Consultant", ["Stakeholder Management", "Data Modelling", "SQL"]),
    ("Engagement Manager", ["Stakeholder Management", "Team Leadership", "Negotiation"]),
    ("Risk", ["SQL", "Statistical Analysis", "R"]),
    ("Quantitative", ["Python", "R", "Statistical Analysis"]),
    ("Process Engineer", ["Statistical Analysis", "Technical Writing", "Python"]),
    ("ASIC", ["C++", "Python", "Technical Writing"]),
    ("Verification", ["C++", "Python", "Agile Delivery"]),
    ("Firmware", ["C++", "C#", "Technical Writing"]),
    ("Embedded", ["C++", "Python", "Technical Writing"]),
    ("Hardware", ["Technical Writing", "Agile Delivery", "Negotiation"]),
    ("Operations", ["SQL", "Stakeholder Management", "Agile Delivery"]),
    ("Merchant", ["Negotiation", "Stakeholder Management", "SQL"]),
    ("Supply Chain", ["SQL", "Statistical Analysis", "Negotiation"]),
    ("Financial", ["SQL", "Statistical Analysis", "R"]),
    ("Compliance", ["Technical Writing", "Stakeholder Management", "SQL"]),
    ("Regulatory", ["Technical Writing", "Stakeholder Management"]),
    ("Marketing", ["A/B Testing", "SQL", "Technical Writing"]),
]
DEFAULT_SKILLS = ["Python", "SQL", "Stakeholder Management", "Agile Delivery", "Technical Writing"]

skill_id = {name: i + 1 for i, (name, _, _) in enumerate(SKILLS)}


def d2s(d):
    if d is None:
        return "NULL"
    if isinstance(d, datetime):
        return "'" + d.strftime("%Y-%m-%d %H:%M:%S") + "'"
    if isinstance(d, date):
        return "'" + d.strftime("%Y-%m-%d") + "'"
    return "'" + str(d).replace("'", "''") + "'"


def rows_sql(table, cols, rows, chunk=40):
    out = []
    for i in range(0, len(rows), chunk):
        block = rows[i:i + chunk]
        out.append(f"INSERT INTO {table} ({', '.join(cols)}) VALUES")
        vals = []
        for r in block:
            def enc(v):
                if v is None:
                    return "NULL"
                if isinstance(v, (int, float)):
                    return str(v)
                return d2s(v)
            vals.append("  (" + ", ".join(enc(v) for v in r) + ")")
        out.append(",\n".join(vals) + ";")
    return "\n".join(out)


def pick(seq):
    return seq[R.randrange(len(seq))]


def weighted(pairs):
    total = sum(w for _, w in pairs)
    x = R.uniform(0, total)
    acc = 0
    for v, w in pairs:
        acc += w
        if x <= acc:
            return v
    return pairs[-1][0]


def rand_dt(start, end):
    span = int((end - start).total_seconds())
    return start + timedelta(seconds=R.randrange(max(span, 1)))


def skills_for_title(title):
    for kw, names in TITLE_SKILLS:
        if kw.lower() in title.lower():
            return names
    return DEFAULT_SKILLS


# ---------------------------------------------------------------- companies
companies = []
for i, (name, ind, ctry, size, founded, verified) in enumerate(COMPANIES, start=1):
    cities = CITY_BY_COUNTRY.get(ctry, CITIES[0][0:1])
    companies.append(dict(id=i, name=name, industry=ind, country=ctry, city=pick(cities),
                          size=size, founded=founded, verified=verified))

# ---------------------------------------------------------------- members
EMAIL_DOMAINS = ["gmail.com", "outlook.com", "proton.me", "mail.com", "yahoo.com"]
members = []
used_names = set()
for i in range(1, 301):
    while True:
        fn, ln = pick(FIRST), pick(LAST)
        nm = f"{fn} {ln}"
        if nm not in used_names:
            used_names.add(nm)
            break
    city, ctry = pick(CITIES)
    years = min(25, max(0, int(R.gauss(7, 5))))
    joined = rand_dt(datetime(2013, 1, 1), datetime(2026, 9, 20)).date()
    is_rec = i <= 72
    if is_rec:
        co = companies[(i - 1) % 60] if i <= 60 else pick(companies)
        title = "Technical Recruiter" if R.random() < 0.7 else "Talent Acquisition Partner"
        years = min(22, max(3, years))
    else:
        co = pick(companies) if R.random() < 0.88 else None
        title = pick(TITLES[co["industry"]]) if co else pick(TITLES["Software"])
    headline = f"{title} at {co['name']}" if co else f"{title} | open to work"
    members.append(dict(id=i, name=nm, headline=headline, email=f"{fn.lower()}.{ln.lower()}{i}@{pick(EMAIL_DOMAINS)}",
                        city=city, country=ctry, years=years, recruiter=is_rec,
                        company=co, title=title, open_to_work=1 if R.random() < (0.62 if is_rec else 0.45) else 0,
                        visibility=weighted([("PUBLIC", 70), ("CONNECTIONS", 25), ("PRIVATE", 5)]),
                        joined=joined))

# ---------------------------------------------------------------- education
education = []
for m in members:
    n = weighted([(1, 70), (2, 28), (3, 2)])
    start = m["joined"].year - max(0, m["years"]) - 4
    start = max(1998, min(2019, start))
    degrees = [("BACHELOR", 60), ("MASTER", 28), ("MBA", 5), ("PHD", 3), ("DIPLOMA", 4)]
    for k in range(n):
        deg = weighted(degrees)
        if k == 0:
            s = start
            e = s + (4 if deg in ("BACHELOR", "MBA") else 2 if deg in ("MASTER", "DIPLOMA") else 5)
        else:
            s = start + 4
            e = s + 2
        education.append(dict(member=m["id"], school=pick([
            "National University of Singapore", "Tsinghua University", "Peking University",
            "University of Hong Kong", "University of Toronto", "University of Melbourne",
            "ETH Zurich", "Technical University of Munich", "Imperial College London",
            "University of California, Berkeley", "Carnegie Mellon University",
            "Georgia Institute of Technology", "University of Tokyo", "Seoul National University",
            "Indian Institute of Technology Bombay", "Shanghai Jiao Tong University"]) ,
            degree=deg, field=pick(["Computer Science", "Information Systems", "Data Science",
                                    "Electrical Engineering", "Mathematics", "Business Administration",
                                    "Statistics", "Human-Computer Interaction"]),
            start=s, end=e))

# ---------------------------------------------------------------- experience
experience = []
for m in members:
    co = m["company"]
    if co is None:
        # past employers only, or no experience at all for fresh graduates
        if m["years"] >= 2:
            k = weighted([(1, 60), (2, 40)])
        else:
            k = 0
        t = 0
        for _ in range(k):
            comp = pick(companies)
            start = datetime(ANCHOR.year - m["years"] + t * 3, R.randint(1, 12), 1).date()
            end = start + timedelta(days=R.randint(400, 1100))
            end = min(end, ANCHOR.date() - timedelta(days=30))
            if end <= start:
                end = start + timedelta(days=400)
            experience.append(dict(member=m["id"], company=comp["id"],
                                   title=pick(TITLES[comp["industry"]]),
                                   start=start, end=end, current=0))
            t += 1
    else:
        k = weighted([(1, 45), (2, 42), (3, 13)])
        # oldest job first
        span = max(1, m["years"]) * 365
        cur_start = ANCHOR.date() - timedelta(days=R.randint(120, min(span, 2600)))
        starts = []
        for j in range(k - 1):
            off = int(span * (k - 1 - j) / k)
            s = max(ANCHOR.date() - timedelta(days=span + 60), cur_start - timedelta(days=off))
            starts.append(s)
        starts = sorted(set(starts))
        for j, s in enumerate(starts):
            e = (starts[j + 1] - timedelta(days=R.randint(5, 40))) if j + 1 < len(starts) \
                else (cur_start - timedelta(days=R.randint(5, 40)))
            if e <= s:
                e = s + timedelta(days=365)
            comp = pick(companies)
            experience.append(dict(member=m["id"], company=comp["id"],
                                   title=pick(TITLES[comp["industry"]]),
                                   start=s, end=e, current=0))
        experience.append(dict(member=m["id"], company=co["id"], title=m["title"],
                               start=cur_start, end=None, current=1))

# ---------------------------------------------------------------- member_skill
member_skill = []
for m in members:
    names = set(skills_for_title(m["title"]))
    while len(names) < weighted([(3, 25), (4, 40), (5, 25), (6, 10)]):
        names.add(pick(SKILLS)[0])
    for nm in names:
        years = min(float(m["years"]), R.uniform(0.5, 12.0))
        prof = 1 + min(4, int(years / 2.5)) + (1 if R.random() < 0.25 else 0)
        prof = max(1, min(5, prof))
        if m["recruiter"] and nm in ("Negotiation", "Stakeholder Management", "Technical Writing"):
            prof = min(5, prof + 1)
        member_skill.append(dict(member=m["id"], skill=skill_id[nm], prof=prof,
                                 years=round(min(20.0, years), 1),
                                 endorse=R.randint(0, 40),
                                 added=rand_dt(datetime(2020, 1, 1), datetime(2026, 9, 1)).date()))

# ---------------------------------------------------------------- jobs
recruiters_by_company = {}
employees_by_company = {}
for m in members:
    if m["company"] is not None:
        employees_by_company.setdefault(m["company"]["id"], []).append(m["id"])
        if m["recruiter"]:
            recruiters_by_company.setdefault(m["company"]["id"], []).append(m["id"])
for cid in range(1, 61):
    employees_by_company.setdefault(cid, [cid])          # company i has recruiter member i
    recruiters_by_company.setdefault(cid, [cid])

jobs = []
for c in companies:
    n_jobs = weighted([(1, 25), (2, 55), (3, 20)])
    for _ in range(n_jobs):
        if len(jobs) >= 120:
            break
        title = pick(TITLES[c["industry"]])
        sen = weighted(SENIORITY)
        lo, hi = SALARY[sen]
        lo = int(lo * R.uniform(0.9, 1.05) / 1000) * 1000
        hi = int(hi * R.uniform(0.95, 1.10) / 1000) * 1000
        posted = rand_dt(datetime(2024, 6, 1), datetime(2026, 9, 10))
        jobs.append(dict(id=len(jobs) + 1, company=c["id"], recruiter=pick(recruiters_by_company[c["id"]]),
                         title=title, seniority=sen, etype=weighted([("FULL_TIME", 86), ("CONTRACT", 8), ("INTERNSHIP", 4), ("PART_TIME", 2)]),
                         mode=weighted([("HYBRID", 50), ("ONSITE", 30), ("REMOTE", 20)]),
                         city=c["city"], country=c["country"],
                         smin=lo, smax=hi, minexp=max(0, ["INTERN", "JUNIOR", "MID", "SENIOR", "LEAD", "PRINCIPAL", "DIRECTOR"].index(sen) * 2 - R.randint(0, 1)),
                         openings=weighted([(1, 55), (2, 30), (3, 10), (5, 5)]),
                         posted=posted, status="OPEN", closed=None))
# trim / extend to exactly 120
while len(jobs) < 120:
    c = pick(companies)
    title = pick(TITLES[c["industry"]])
    sen = weighted(SENIORITY)
    lo, hi = SALARY[sen]
    posted = rand_dt(datetime(2024, 6, 1), datetime(2026, 9, 10))
    jobs.append(dict(id=len(jobs) + 1, company=c["id"], recruiter=pick(recruiters_by_company[c["id"]]),
                     title=title, seniority=sen, etype="FULL_TIME", mode="HYBRID",
                     city=c["city"], country=c["country"], smin=lo, smax=hi, minexp=0,
                     openings=1, posted=posted, status="OPEN", closed=None))

# draft postings carry no applications
draft_ids = set(R.sample([j["id"] for j in jobs], 5))
for j in jobs:
    if j["id"] in draft_ids:
        j["status"] = "DRAFT"

# ---------------------------------------------------------------- job_skill
job_skill = []
for j in jobs:
    core = skills_for_title(j["title"])
    chosen = []
    for nm in core:
        if nm not in chosen:
            chosen.append(nm)
    while len(chosen) < weighted([(3, 20), (4, 50), (5, 30)]):
        cand = pick(SKILLS)[0]
        if cand not in chosen:
            chosen.append(cand)
    for k, nm in enumerate(chosen):
        imp = "REQUIRED" if k < max(2, len(chosen) - 1) else "PREFERRED"
        if R.random() < 0.15:
            imp = "PREFERRED" if imp == "REQUIRED" else "REQUIRED"
        job_skill.append(dict(job=j["id"], skill=skill_id[nm], importance=imp,
                              minp=4 if imp == "REQUIRED" else 3))

# every posting must ask for at least three hard requirements (two if it
# only lists three skills in total), otherwise the skill-gap queries compare
# against a one-item list and the result is noise.  Deterministic pass, it
# consumes no randomness.
by_job = {}
for idx, js in enumerate(job_skill):
    by_job.setdefault(js["job"], []).append(idx)
for jid, idxs in by_job.items():
    required = [i for i in idxs if job_skill[i]["importance"] == "REQUIRED"]
    floor = 3 if len(idxs) >= 3 else 2
    if len(required) < floor:
        for i in idxs:
            if len(required) >= floor:
                break
            if job_skill[i]["importance"] == "PREFERRED":
                job_skill[i]["importance"] = "REQUIRED"
                job_skill[i]["minp"] = 4
                required.append(i)

# ---------------------------------------------------------------- applications
candidate_ids = [m["id"] for m in members if not m["recruiter"]]
member_by_id = {m["id"]: m for m in members}
candidate_company = {m["id"]: (m["company"]["id"] if m["company"] else None) for m in members}
job_by_id = {j["id"]: j for j in jobs}
open_jobs = [j for j in jobs if j["status"] != "DRAFT"]

pairs = set()
apps = []
attempts = 0
while len(apps) < 250 and attempts < 200000:
    attempts += 1
    j = pick(open_jobs)
    m_id = pick(candidate_ids)
    if candidate_company[m_id] == j["company"]:
        continue
    key = (j["id"], m_id)
    if key in pairs:
        continue
    pairs.add(key)
    apps.append(dict(job=j, member=m_id))

# channel mix
channels = ["REFERRAL"] * 60 + ["SOURCING"] * 40 + ["DIRECT"] * 150
R.shuffle(channels)

STATUS_PLAN = {
    "REFERRAL": [("HIRED", 10), ("OFFER", 6), ("INTERVIEW", 10), ("SCREENING", 8),
                 ("SUBMITTED", 12), ("REJECTED", 10), ("WITHDRAWN", 4)],
    "SOURCING": [("HIRED", 3), ("OFFER", 3), ("INTERVIEW", 8), ("SCREENING", 8),
                 ("SUBMITTED", 9), ("REJECTED", 7), ("WITHDRAWN", 2)],
    "DIRECT":   [("HIRED", 9), ("OFFER", 5), ("INTERVIEW", 22), ("SCREENING", 29),
                 ("SUBMITTED", 34), ("REJECTED", 41), ("WITHDRAWN", 10)],
}
status_pool = []
for ch, plan in STATUS_PLAN.items():
    for st, n in plan:
        status_pool.extend([(ch, st)] * n)
R.shuffle(status_pool)
# keep the per-channel counts exact by sorting deterministically
by_channel = {}
for ch, st in status_pool:
    by_channel.setdefault(ch, []).append(st)

# assign channel quotas to applications: first 60 shuffled apps get REFERRAL etc.
app_channels = ["REFERRAL"] * 60 + ["SOURCING"] * 40 + ["DIRECT"] * 150
R.shuffle(app_channels)
for a, ch in zip(apps, app_channels):
    a["channel"] = ch

# draw status per channel
for ch in ("REFERRAL", "SOURCING", "DIRECT"):
    sts = by_channel[ch][:]
    R.shuffle(sts)
    idxs = [i for i, a in enumerate(apps) if a["channel"] == ch]
    for i, st in zip(idxs, sts):
        apps[i]["status"] = st

# hires must not exceed openings
hire_count = {}
for a in apps:
    jid = a["job"]["id"]
    if a["status"] == "HIRED":
        hire_count[jid] = hire_count.get(jid, 0) + 1
        if hire_count[jid] > a["job"]["openings"]:
            a["status"] = "REJECTED"
            hire_count[jid] -= 1

# timestamps
for a in apps:
    j = a["job"]
    latest_apply = min(ANCHOR - timedelta(days=35), j["posted"] + timedelta(days=120))
    earliest = j["posted"] + timedelta(hours=R.randint(2, 72))
    if latest_apply <= earliest:
        latest_apply = earliest + timedelta(days=1)
    a["applied"] = rand_dt(earliest, latest_apply)

# ---------------------------------------------------------------- interviews
interviewer_pool = {}
for cid, ids in employees_by_company.items():
    interviewer_pool[cid] = sorted(set(ids))

interviews = []
for a in apps:
    st = a["status"]
    j = a["job"]
    n = 0
    if st == "HIRED":
        n = weighted([(3, 70), (4, 30)])
    elif st == "OFFER":
        n = weighted([(2, 40), (3, 60)])
    elif st == "INTERVIEW":
        n = weighted([(1, 55), (2, 45)])
    elif st == "REJECTED":
        n = weighted([(0, 55), (1, 30), (2, 15)])
    elif st == "WITHDRAWN":
        n = weighted([(0, 60), (1, 40)])
    a["n_int"] = n
    t = a["applied"] + timedelta(days=R.randint(3, 9), hours=R.randint(0, 6))
    seq = []
    for r in range(1, n + 1):
        if r > 1:
            t = t + timedelta(days=R.randint(5, 12), hours=R.randint(0, 5))
        if t > ANCHOR - timedelta(days=3):
            t = ANCHOR - timedelta(days=3)
        pool = [x for x in interviewer_pool[j["company"]] if x != a["member"]]
        if not pool:
            pool = [x for x in interviewer_pool[j["company"]]]
        seq.append(t)
        iv_type = ["PHONE", "VIDEO", "TECHNICAL", "ONSITE", "HR"][min(r - 1, 4)]
        if r == 1 and R.random() < 0.5:
            iv_type = "PHONE"
        interviews.append(dict(app=a, round=r, type=iv_type, when=t,
                               dur=weighted([(30, 30), (45, 45), (60, 25)]),
                               interviewer=pick(pool), status=st))
    # outcomes
    for k, iv in enumerate(interviews[-n:] if n else []):
        last = (k == n - 1)
        if st == "REJECTED":
            iv["outcome"] = "PENDING" if not last else "FAIL"
        elif st == "WITHDRAWN":
            iv["outcome"] = "PASS" if not last else "PENDING"
        elif st == "INTERVIEW":
            iv["outcome"] = "PENDING" if last else "PASS"
        else:
            iv["outcome"] = "PASS"
        iv["score"] = None if iv["outcome"] == "PENDING" else R.choice([3, 4, 4, 5, 5, 2])
    a["interviews"] = interviews[-n:] if n else []

# decided_at
for a in apps:
    st = a["status"]
    if st in ("SUBMITTED", "SCREENING", "INTERVIEW"):
        a["decided"] = None
        continue
    base = a["interviews"][-1]["when"] if a["interviews"] else a["applied"]
    if st == "WITHDRAWN":
        d = a["applied"] + timedelta(days=R.randint(2, 18))
    elif st == "REJECTED":
        d = base + timedelta(days=R.randint(2, 14))
    elif st == "OFFER":
        d = base + timedelta(days=R.randint(2, 7))
    else:  # HIRED
        d = base + timedelta(days=R.randint(5, 15))
    if d > ANCHOR - timedelta(days=2):
        d = ANCHOR - timedelta(days=2)
    if d < a["applied"]:
        d = a["applied"] + timedelta(days=1)
    # keep interviews before the decision
    for iv in a["interviews"]:
        if iv["when"] > d - timedelta(hours=6):
            shift = d - timedelta(days=2) - iv["when"]
            iv["when"] += shift
    a["decided"] = d

# ---------------------------------------------------------------- referrals
referral = []
for a in apps:
    if a["channel"] != "REFERRAL":
        continue
    j = a["job"]
    pool = [x for x in interviewer_pool[j["company"]] if x != a["member"]]
    if not pool:
        a["channel"] = "DIRECT"
        continue
    ref = pick(pool)
    if ref == a["member"]:
        a["channel"] = "DIRECT"
        continue
    rel = weighted([("COLLEAGUE", 55), ("FORMER_COLLEAGUE", 15), ("CLASSMATE", 20), ("FRIEND", 10)])
    referred = a["applied"] - timedelta(days=R.randint(0, 6), hours=R.randint(1, 20))
    if referred < j["posted"]:
        referred = j["posted"] + timedelta(hours=R.randint(1, 48))
    if a["status"] == "HIRED":
        amt = float(R.choice([2000, 2500, 3000, 3500, 4000, 5000]))
        bstat = "PAID" if a["decided"] < ANCHOR - timedelta(days=45) else "PENDING"
    elif a["status"] in ("OFFER", "INTERVIEW"):
        amt = float(R.choice([1500, 2000, 2500]))
        bstat = "PENDING"
    elif a["status"] in ("REJECTED", "WITHDRAWN"):
        amt = float(R.choice([1500, 2000]))
        bstat = "FORFEITED"
    else:
        amt = float(R.choice([1500, 2000, 2500]))
        bstat = "NONE"
    referral.append(dict(app=a, referrer=ref, rel=rel, when=referred, amount=amt, bstatus=bstat))

# ---------------------------------------------------------------- connections
edges = set()
edge_pairs = set()


def add_edge(a, b, when, kind):
    if a == b:
        return
    lo, hi = (a, b) if a < b else (b, a)
    if (lo, hi) in edge_pairs:
        return
    edge_pairs.add((lo, hi))
    edges.add((lo, hi, when, kind))


# colleagues inside a company
for cid, ids in employees_by_company.items():
    ids = sorted(set(ids))
    for i in range(len(ids)):
        for k in range(i + 1, len(ids)):
            if R.random() < 0.45:
                add_edge(ids[i], ids[k], rand_dt(datetime(2019, 1, 1), datetime(2026, 9, 1)),
                         "COLLEAGUE")
# random acquaintances
for _ in range(760):
    a, b = R.sample(range(1, 301), 2)
    add_edge(a, b, rand_dt(datetime(2018, 1, 1), datetime(2026, 9, 1)),
             weighted([("CLASSMATE", 35), ("FRIEND", 45), ("FOLLOW", 20)]))
# referrer and candidate know each other
for r in referral:
    kind = r["rel"] if r["rel"] in ("COLLEAGUE", "CLASSMATE", "FRIEND", "FOLLOW") else "COLLEAGUE"
    add_edge(r["referrer"], r["app"]["member"],
             r["when"] - timedelta(days=R.randint(30, 900)), kind)

# ---------------------------------------------------------------- write
lines = []
lines.append("""-- =====================================================================
-- LinkedIn, reverse-engineered: seed data
-- 02_seed.sql  |  MySQL 8.0  |  utf8mb4
--
-- Generated deterministically (seed 20261115) by _work/gen_seed.py.
-- Snapshot date: 2026-10-15 18:00.  Every timestamp is <= the snapshot.
--
-- Consistency invariants baked into this file (each one is asserted by
-- the checks in design/Constraint_Inventory.md and re-verified by
-- _work/verify_data.py):
--   I1  an application is HIRED only if it has 3 PASS interviews
--   I2  an application is REJECTED after interviews only if its last
--       interview outcome is FAIL
--   I3  decided_at is NULL exactly for SUBMITTED / SCREENING / INTERVIEW
--   I4  every REFERRAL application has a referral row, and the referrer
--       is currently employed by the hiring company
--   I5  hires per posting <= postings.openings
--   I6  a member has at most one experience row with is_current = 1
--   I7  connected edges are stored once, member_a_id < member_b_id
--   I8  applied_at >= posted_at and decided_at >= applied_at
-- =====================================================================

USE linkedin_db;
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;
""")

lines.append("-- ---------------------------------------------------------------- company")
lines.append(rows_sql("company",
                      ["company_id", "company_name", "industry", "hq_country", "size_band",
                       "founded_year", "is_verified"],
                      [(c["id"], c["name"], c["industry"], c["country"], c["size"],
                        c["founded"], c["verified"]) for c in companies]))

lines.append("\n-- ---------------------------------------------------------------- member")
lines.append(rows_sql("member",
                      ["member_id", "full_name", "headline", "email", "country", "city",
                       "years_experience", "open_to_work", "profile_visibility", "joined_at"],
                      [(m["id"], m["name"], m["headline"], m["email"], m["country"], m["city"],
                        m["years"], m["open_to_work"], m["visibility"], m["joined"])
                       for m in members]))

lines.append("\n-- ---------------------------------------------------------------- skill")
lines.append(rows_sql("skill", ["skill_id", "skill_name", "skill_family", "is_emerging"],
                      [(i + 1, s[0], s[1], s[2]) for i, s in enumerate(SKILLS)]))

lines.append("\n-- ---------------------------------------------------------------- education")
lines.append(rows_sql("education",
                      ["member_id", "school_name", "degree", "field_of_study", "start_year", "end_year"],
                      [(e["member"], e["school"], e["degree"], e["field"], e["start"], e["end"])
                       for e in sorted(education, key=lambda x: (x["member"], x["start"]))]))

lines.append("\n-- ---------------------------------------------------------------- experience")
lines.append(rows_sql("experience",
                      ["member_id", "company_id", "title", "start_date", "end_date", "is_current"],
                      [(e["member"], e["company"], e["title"], e["start"],
                        e["end"], e["current"])
                       for e in sorted(experience, key=lambda x: (x["member"], x["start"]))]))

lines.append("\n-- ---------------------------------------------------------------- job_posting")
lines.append(rows_sql("job_posting",
                      ["job_id", "company_id", "recruiter_id", "title", "seniority",
                       "employment_type", "work_mode", "city", "country", "salary_min",
                       "salary_max", "currency", "min_years_experience", "openings", "status",
                       "posted_at", "closed_at"],
                      [(j["id"], j["company"], j["recruiter"], j["title"], j["seniority"],
                        j["etype"], j["mode"], j["city"], j["country"], j["smin"], j["smax"],
                        "USD", j["minexp"], j["openings"], j["status"], j["posted"],
                        j["closed"]) for j in jobs]))

lines.append("\n-- ---------------------------------------------------------------- job_skill")
lines.append(rows_sql("job_skill", ["job_id", "skill_id", "importance", "min_proficiency"],
                      [(js["job"], js["skill"], js["importance"], js["minp"]) for js in job_skill]))

lines.append("\n-- ---------------------------------------------------------------- member_skill")
lines.append(rows_sql("member_skill",
                      ["member_id", "skill_id", "proficiency", "years_used", "endorsement_count", "added_at"],
                      [(ms["member"], ms["skill"], ms["prof"], ms["years"], ms["endorse"], ms["added"])
                       for ms in sorted(member_skill, key=lambda x: (x["member"], x["skill"]))]))

lines.append("\n-- ---------------------------------------------------------------- application")
lines.append(rows_sql("application",
                      ["application_id", "job_id", "member_id", "source_channel", "status",
                       "applied_at", "decided_at", "resume_version"],
                      [(i + 1, a["job"]["id"], a["member"], a["channel"], a["status"],
                        a["applied"], a["decided"], "v" + str(R.randint(1, 4)))
                       for i, a in enumerate(apps)]))

app_id = {id(a): i + 1 for i, a in enumerate(apps)}

lines.append("\n-- ---------------------------------------------------------------- interview")
lines.append(rows_sql("interview",
                      ["application_id", "round_no", "interview_type", "scheduled_at",
                       "duration_min", "interviewer_id", "outcome", "score"],
                      [(app_id[id(iv["app"])], iv["round"], iv["type"], iv["when"], iv["dur"],
                        iv["interviewer"], iv["outcome"], iv["score"]) for iv in interviews]))

lines.append("\n-- ---------------------------------------------------------------- referral")
lines.append(rows_sql("referral",
                      ["application_id", "referrer_id", "relationship", "referred_at",
                       "bonus_amount", "bonus_status"],
                      [(app_id[id(r["app"])], r["referrer"], r["rel"], r["when"],
                        "%.2f" % r["amount"], r["bstatus"]) for r in referral]))

lines.append("\n-- ---------------------------------------------------------------- connection")
lines.append(rows_sql("connection", ["member_a_id", "member_b_id", "connected_at", "connection_type"],
                      sorted([(a, b, w, k) for (a, b, w, k) in edges],
                             key=lambda x: (x[0], x[1]))))

# close some postings after their last application
close_lines = []
closed_jobs = 0
for j in jobs:
    j_apps = [a for a in apps if a["job"]["id"] == j["id"]]
    hires = sum(1 for a in j_apps if a["status"] == "HIRED")
    last = max([a["decided"] or a["applied"] for a in j_apps], default=j["posted"])
    if j["status"] == "DRAFT":
        continue
    if hires >= j["openings"]:
        closed = min(ANCHOR - timedelta(days=1), last + timedelta(days=R.randint(2, 12)))
        close_lines.append(f"UPDATE job_posting SET status = 'CLOSED', closed_at = {d2s(closed)} "
                           f"WHERE job_id = {j['id']};")
        closed_jobs += 1
    elif hires == 0 and j_apps and R.random() < 0.18:
        closed = min(ANCHOR - timedelta(days=1), last + timedelta(days=R.randint(5, 40)))
        close_lines.append(f"UPDATE job_posting SET status = 'CLOSED', closed_at = {d2s(closed)} "
                           f"WHERE job_id = {j['id']};")
        closed_jobs += 1
# a few postings on hold
for jid in R.sample([j["id"] for j in jobs if j["status"] == "OPEN"], 4):
    close_lines.append(f"UPDATE job_posting SET status = 'ON_HOLD' WHERE job_id = {jid};")

lines.append("\n-- ---------------------------------------------------------------- posting lifecycle")
lines.append("-- Postings are closed only after their last application/decision, so no\n"
             "-- application can be dated after the closing of its posting (I8).")
lines.extend(close_lines)

lines.append("""
SET FOREIGN_KEY_CHECKS = 1;

-- Sanity: the row counts a marker script expects.
SELECT 'company' AS tbl, COUNT(*) AS n FROM company
UNION ALL SELECT 'member', COUNT(*) FROM member
UNION ALL SELECT 'skill', COUNT(*) FROM skill
UNION ALL SELECT 'job_posting', COUNT(*) FROM job_posting
UNION ALL SELECT 'job_skill', COUNT(*) FROM job_skill
UNION ALL SELECT 'member_skill', COUNT(*) FROM member_skill
UNION ALL SELECT 'education', COUNT(*) FROM education
UNION ALL SELECT 'experience', COUNT(*) FROM experience
UNION ALL SELECT 'application', COUNT(*) FROM application
UNION ALL SELECT 'interview', COUNT(*) FROM interview
UNION ALL SELECT 'referral', COUNT(*) FROM referral
UNION ALL SELECT 'connection', COUNT(*) FROM connection;
""")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines))

stats = dict(companies=len(companies), members=len(members), skills=len(SKILLS), jobs=len(jobs),
             job_skill=len(job_skill), member_skill=len(member_skill), education=len(education),
             experience=len(experience), applications=len(apps), interviews=len(interviews),
             referral=len(referral), connection=len(edges), closed_jobs=closed_jobs,
             hires=sum(1 for a in apps if a["status"] == "HIRED"),
             status_mix={st: sum(1 for a in apps if a["status"] == st)
                         for st in ["SUBMITTED", "SCREENING", "INTERVIEW", "OFFER", "HIRED",
                                    "REJECTED", "WITHDRAWN"]},
             channel_mix={ch: sum(1 for a in apps if a["channel"] == ch)
                          for ch in ["DIRECT", "REFERRAL", "SOURCING"]})
json.dump(stats, open(STATS, "w", encoding="utf-8"), indent=2)
print(json.dumps(stats, indent=2))
print("wrote", OUT, os.path.getsize(OUT), "bytes")
