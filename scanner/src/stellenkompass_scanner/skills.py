"""Find well-known skills (languages, frameworks, tools) in a job's title and description."""

from __future__ import annotations

import re

# (skill, pattern). Patterns are case-insensitive unless the skill is in _CASE_SENSITIVE.
_SKILLS: tuple[tuple[str, str], ...] = (
    ("Python", r"python"),
    ("Java", r"java(?![ -]?script)"),
    ("JavaScript", r"javascript|\bjs\b"),
    ("TypeScript", r"typescript"),
    ("Go", r"golang|\bGo\b(?=\s*(?:,|/|\)|and\b|or\b|developer|engineer|backend|services))|"
           r"(?<=[,/(] )Go\b|(?<=[,/(])Go\b"),
    ("Rust", r"\brust\b"),
    ("C++", r"c\+\+"),
    ("C#", r"c#|\.net\b"),
    ("Kotlin", r"kotlin"),
    ("Swift", r"\bswift\b"),
    ("Scala", r"\bscala\b"),
    ("R", r"(?<![\w-])R(?=\s*(?:,|/|and\b|or\b|&)\s*(?:Python|SQL|SAS|Matlab|Stata))|"
          r"(?<=Python)\s*(?:,|/|and|or|&)\s*R(?![\w+#-])|RStudio"),
    ("PHP", r"\bphp\b"),
    ("Ruby", r"\bruby\b|\brails\b"),
    ("SQL", r"\bsql\b|postgres|mysql|t-sql"),
    ("React", r"\breact(?:\.js|js)?\b(?! native)"),
    ("React Native", r"react native"),
    ("Angular", r"\bangular\b"),
    ("Vue", r"\bvue(?:\.js|js)?\b"),
    ("Node.js", r"\bnode(?:\.js|js)\b|\bnode\b(?= ?/| backend)"),
    ("Next.js", r"next\.js|nextjs"),
    ("Django", r"django"),
    ("FastAPI", r"fastapi"),
    ("Flask", r"\bflask\b"),
    ("Spring", r"spring boot|\bspring\b(?= framework)"),
    ("GraphQL", r"graphql"),
    ("PostgreSQL", r"postgres(?:ql)?"),
    ("MongoDB", r"mongodb|\bmongo\b"),
    ("Redis", r"\bredis\b"),
    ("Elasticsearch", r"elasticsearch|opensearch"),
    ("Kafka", r"\bkafka\b"),
    ("Spark", r"\bspark\b|pyspark"),
    ("Airflow", r"airflow"),
    ("dbt", r"\bdbt\b"),
    ("Snowflake", r"snowflake"),
    ("Databricks", r"databricks"),
    ("BigQuery", r"bigquery"),
    ("Pandas", r"\bpandas\b"),
    ("Machine Learning", r"machine learning|maschinelles lernen|\bml\b"),
    ("Deep Learning", r"deep learning"),
    ("PyTorch", r"pytorch"),
    ("TensorFlow", r"tensorflow|keras"),
    ("scikit-learn", r"scikit-learn|sklearn"),
    ("NLP", r"\bnlp\b|natural language processing"),
    ("Computer Vision", r"computer vision|bildverarbeitung"),
    ("LLM", r"\bllms?\b|large language model|generative ai|\bgenai\b|\brag\b"),
    ("MLOps", r"mlops"),
    ("Data Science", r"data scien"),
    ("Statistics", r"statistic|statistik"),
    ("AWS", r"\baws\b|amazon web services"),
    ("Azure", r"\bazure\b"),
    ("GCP", r"\bgcp\b|google cloud"),
    ("Docker", r"docker|container"),
    ("Kubernetes", r"kubernetes|\bk8s\b"),
    ("Terraform", r"terraform"),
    ("CI/CD", r"ci/cd|continuous integration|github actions|gitlab ci|jenkins"),
    ("Linux", r"\blinux\b"),
    ("Git", r"\bgit\b"),
    ("Microservices", r"microservice"),
    ("REST APIs", r"(?i:restful|\brest[ -]?apis?\b)|\bREST\b"),
    ("Excel", r"\bexcel\b"),
    ("Power BI", r"power ?bi"),
    ("Tableau", r"tableau"),
    ("SAP", r"\bsap\b"),
    ("Salesforce", r"salesforce"),
    ("Figma", r"figma"),
    ("Jira", r"\bjira\b"),
    ("Agile", r"\bagile\b|\bagil\b|scrum|kanban"),
    ("SEO", r"\bseo\b"),
    ("Embedded", r"embedded"),
    ("MATLAB", r"matlab"),
    ("CAD", r"\bcad\b|solidworks|catia"),
)  # fmt: skip
_CASE_SENSITIVE = {"Go", "R", "REST APIs"}

_COMPILED = tuple(
    (name, re.compile(pattern, 0 if name in _CASE_SENSITIVE else re.IGNORECASE))
    for name, pattern in _SKILLS
)
SKILL_NAMES = tuple(name for name, _ in _SKILLS)


def extract_skills(text: str, limit: int = 12) -> list[str]:
    """Skills mentioned in the text, in the order of the list above (stable for the UI)."""
    text = text or ""
    return [name for name, pattern in _COMPILED if pattern.search(text)][:limit]
