"""Data analysis with Python + SQL on the public Titanic passenger dataset (891 rows).
Loads the CSV into an in-memory SQLite database, cleans it, runs SQL queries, saves charts and a text report.
"""
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams["svg.fonttype"] = "none"

df = pd.read_csv("data/titanic.csv")
print("Rows:", len(df))
print("Missing values per column (before cleaning):")
print(df.isna().sum()[df.isna().sum() > 0].to_string(), "\n")

# Cleaning: fill missing age with the median age of the passenger's class and sex; drop 'deck' (77% missing).
df["age"] = df.groupby(["pclass", "sex"])["age"].transform(lambda s: s.fillna(s.median()))
df["embark_town"] = df["embark_town"].fillna("Unknown")
df = df.drop(columns=["deck"])

con = sqlite3.connect(":memory:")
df.to_sql("passengers", con, index=False)

queries = {
 "Overall survival rate": """
   SELECT COUNT(*) AS passengers, SUM(survived) AS survivors,
          ROUND(100.0*SUM(survived)/COUNT(*),1) AS survival_pct
   FROM passengers""",
 "Survival by sex": """
   SELECT sex, COUNT(*) AS passengers, ROUND(100.0*AVG(survived),1) AS survival_pct
   FROM passengers GROUP BY sex ORDER BY survival_pct DESC""",
 "Survival by ticket class": """
   SELECT pclass, COUNT(*) AS passengers, ROUND(100.0*AVG(survived),1) AS survival_pct,
          ROUND(AVG(fare),2) AS avg_fare
   FROM passengers GROUP BY pclass ORDER BY pclass""",
 "Survival by age group": """
   SELECT CASE WHEN age < 13 THEN '1. Child (<13)'
               WHEN age < 20 THEN '2. Teen (13-19)'
               WHEN age < 40 THEN '3. Adult (20-39)'
               WHEN age < 60 THEN '4. Middle (40-59)'
               ELSE '5. Senior (60+)' END AS age_group,
          COUNT(*) AS passengers, ROUND(100.0*AVG(survived),1) AS survival_pct
   FROM passengers GROUP BY age_group ORDER BY age_group""",
 "Survival by sex and class": """
   SELECT sex, pclass, COUNT(*) AS passengers, ROUND(100.0*AVG(survived),1) AS survival_pct
   FROM passengers GROUP BY sex, pclass ORDER BY sex, pclass""",
 "Survival by embarkation town": """
   SELECT embark_town, COUNT(*) AS passengers, ROUND(100.0*AVG(survived),1) AS survival_pct
   FROM passengers GROUP BY embark_town ORDER BY passengers DESC""",
 "Travelling alone vs with family": """
   SELECT CASE WHEN alone=1 THEN 'alone' ELSE 'with family' END AS travel,
          COUNT(*) AS passengers, ROUND(100.0*AVG(survived),1) AS survival_pct
   FROM passengers GROUP BY travel""",
}

report = []
tables = {}
for title, q in queries.items():
    t = pd.read_sql_query(q, con)
    tables[title] = t
    block = f"== {title} ==\n{t.to_string(index=False)}\n"
    print(block); report.append(block)
open("report.txt", "w").write("\n".join(report))

fig, axes = plt.subplots(1, 3, figsize=(14, 4))
for ax, (title, x) in zip(axes, [("Survival by sex", "sex"), ("Survival by ticket class", "pclass"),
                                 ("Survival by age group", "age_group")]):
    t = tables[title]
    ax.bar(t[x].astype(str), t["survival_pct"], color="#3b7dd8")
    ax.set_title(title); ax.set_ylabel("Survival %"); ax.set_ylim(0, 100)
    ax.tick_params(axis="x", labelsize=7)
fig.tight_layout(); fig.savefig("survival_charts.png", dpi=120); fig.savefig("survival_charts.svg")
