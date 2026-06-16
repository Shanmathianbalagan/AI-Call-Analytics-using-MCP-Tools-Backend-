import json
import os
from collections import Counter

import mysql.connector
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "call_analytics_db")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
TABLE_NAME = "calls"

mcp = FastMCP("Optimized MySQL Call Dataset MCP Server")


IMPORTANT_COLUMNS = [
    "id",
    "recording_id",
    "call_uuid",
    "call_date",
    "language",
    "gender",
    "overall_score",
    "positive_sentiment",
    "negative_sentiment",
    "neutral_sentiment",
    "products_discussed",
    "focus_areas",
    "call_summary"
]

ISSUE_KEYWORDS = {
    "pricing_or_offers": [
        "price",
        "pricing",
        "discount",
        "offer",
        "cashback",
        "emi",
        "budget",
        "cost",
        "expensive",
    ],
    "warranty_or_claims": [
        "warranty",
        "claim",
        "damage",
        "protection",
        "lost",
        "theft",
        "insurance",
    ],
    "product_availability": [
        "available",
        "availability",
        "stock",
        "model",
        "variant",
        "color",
    ],
    "exchange_or_upgrade": [
        "exchange",
        "upgrade",
        "old phone",
        "old device",
    ],
    "communication_quality": [
        "communication",
        "explain",
        "clarity",
        "clear",
        "confirm",
        "closing",
        "greeting",
        "listening",
    ],
    "customer_support": [
        "support",
        "issue",
        "problem",
        "resolution",
        "assist",
        "invoice",
        "bill",
        "imei",
    ],
}

IMPROVEMENT_KEYWORDS = {
    "greeting": ["greeting", "welcome", "opening", "introduction"],
    "listening_skills": ["listening", "listen", "acknowledge"],
    "probing": ["probing", "probe", "ask", "question", "eligibility"],
    "closure": ["closure", "closing", "confirm", "resolution"],
    "offer_explanation": ["offer", "discount", "cashback", "emi", "explain"],
    "personalization": ["personalized", "name", "preference", "usage"],
}


def get_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        port=MYSQL_PORT
    )


def get_all_columns():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(f"DESCRIBE `{TABLE_NAME}`")
    columns = [row["Field"] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return columns


def shorten_text(value, max_chars=200):
    if value is None:
        return ""

    value = str(value).strip()

    if len(value) > max_chars:
        return value[:max_chars] + "..."

    return value


def clean_compact_row(row):
    cleaned = {}

    for key, value in row.items():
        if isinstance(value, str):
            cleaned[key] = shorten_text(value, 200)
        else:
            cleaned[key] = value

    return cleaned


def clean_full_row(row):
    cleaned = {}

    for key, value in row.items():
        if isinstance(value, str):
            cleaned[key] = value.strip()
        else:
            cleaned[key] = value

    return cleaned


def normalize_date_value(value):
    """
    Convert empty date values to None and keep valid date strings trimmed.
    """

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    return value


def build_date_filter(start_date=None, end_date=None):
    """
    Build a safe SQL date filter for optional call_date filtering.
    """

    start_date = normalize_date_value(start_date)
    end_date = normalize_date_value(end_date)

    conditions = []
    params = []

    if start_date:
        conditions.append("`call_date` >= %s")
        params.append(start_date)

    if end_date:
        conditions.append("`call_date` <= %s")
        params.append(end_date)

    return " AND ".join(conditions), params


def build_where_clause(base_condition=None, start_date=None, end_date=None):
    """
    Combine an optional base SQL condition with optional date filtering.
    """

    conditions = []
    params = []

    if base_condition:
        conditions.append(f"({base_condition})")

    date_condition, date_params = build_date_filter(start_date, end_date)

    if date_condition:
        conditions.append(date_condition)
        params.extend(date_params)

    if not conditions:
        return "", params

    return "WHERE " + " AND ".join(conditions), params


def get_date_filter_metadata(start_date=None, end_date=None):
    """
    Return consistent metadata that explains whether date filtering was used.
    """

    start_date = normalize_date_value(start_date)
    end_date = normalize_date_value(end_date)

    return {
        "start_date": start_date,
        "end_date": end_date,
        "applied": bool(start_date or end_date)
    }


def safe_limit(limit, default=10, maximum=50):
    """
    Keep analytics output compact and avoid huge responses.
    """

    try:
        limit = int(limit)
    except (TypeError, ValueError):
        return default

    if limit < 1:
        return default

    return min(limit, maximum)


def parse_text_items(value):
    """
    Convert JSON-like list strings or plain text into clean text items.
    """

    if value is None:
        return []

    value = str(value).strip()

    if not value:
        return []

    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError:
        return [value]

    if isinstance(parsed_value, list):
        return [
            str(item).strip()
            for item in parsed_value
            if str(item).strip()
        ]

    return [str(parsed_value).strip()]


def normalize_category(text, category_keywords, default_category="other"):
    """
    Map free text to a compact analytics category using keyword matching.
    """

    text = str(text).lower()

    for category, keywords in category_keywords.items():
        if any(keyword in text for keyword in keywords):
            return category

    return default_category


def fetch_analysis_rows(columns, start_date=None, end_date=None):
    """
    Fetch only the columns needed for analytics, with optional date filtering.
    """

    selected_columns = ", ".join([f"`{column}`" for column in columns])
    where_clause, date_params = build_where_clause(
        start_date=start_date,
        end_date=end_date
    )

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        f"""
        SELECT {selected_columns}
        FROM `{TABLE_NAME}`
        {where_clause}
        """,
        date_params
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows


def format_counter(counter, limit):
    """
    Convert a Counter into ranked compact dictionaries.
    """

    return [
        {
            "rank": index,
            "name": name,
            "frequency": frequency,
        }
        for index, (name, frequency) in enumerate(
            counter.most_common(limit),
            start=1
        )
    ]


def build_issue_pattern_result(
    rows,
    start_date=None,
    end_date=None,
    limit=10,
    minimum_frequency=1
):
    """
    Build compact issue analytics from selected call text fields.
    """

    issue_counter = Counter()
    sample_counter = {}
    trend_counter = Counter()

    for row in rows:
        text_items = []

        for column in ["focus_areas", "areas_of_improvement", "call_summary"]:
            text_items.extend(parse_text_items(row.get(column)))

        if row.get("final_conclusion"):
            text_items.append(f"final_conclusion score {row['final_conclusion']}")

        try:
            negative_sentiment = float(row.get("negative_sentiment") or 0)
        except (TypeError, ValueError):
            negative_sentiment = 0

        if negative_sentiment > 0:
            text_items.append("negative sentiment present")

        for item in text_items:
            category = normalize_category(item, ISSUE_KEYWORDS)
            issue_counter[category] += 1
            trend_counter[row.get("call_date", "unknown")] += 1

            if category not in sample_counter:
                sample_counter[category] = shorten_text(item, 180)

    filtered_issues = Counter(
        {
            issue: frequency
            for issue, frequency in issue_counter.items()
            if frequency >= minimum_frequency
        }
    )

    grouped_issues = []

    for index, (issue, frequency) in enumerate(
        filtered_issues.most_common(limit),
        start=1
    ):
        grouped_issues.append(
            {
                "rank": index,
                "issue_category": issue,
                "frequency": frequency,
                "sample_evidence": sample_counter.get(issue, ""),
            }
        )

    return {
        "date_filter": get_date_filter_metadata(start_date, end_date),
        "total_records_analyzed": len(rows),
        "grouped_issues": grouped_issues,
        "issue_trends_by_date": format_counter(trend_counter, limit),
    }


@mcp.tool()
def get_mysql_dataset_summary(
    limit: int = 3,
    start_date=None,
    end_date=None
) -> dict:
    """
    Return dataset summary and full sample records without trimming.
    Optionally filter records by call_date.
    """

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    where_clause, date_params = build_where_clause(
        start_date=start_date,
        end_date=end_date
    )

    cursor.execute(
        f"""
        SELECT COUNT(*) AS total_records
        FROM `{TABLE_NAME}`
        {where_clause}
        """,
        date_params
    )
    total_records = cursor.fetchone()["total_records"]

    columns = get_all_columns()

    cursor.execute(
        f"""
        SELECT *
        FROM `{TABLE_NAME}`
        {where_clause}
        LIMIT %s
        """,
        date_params + [limit]
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "database": MYSQL_DATABASE,
        "table": TABLE_NAME,
        "total_records": total_records,
        "total_columns": len(columns),
        "columns": columns,
        "date_filter": get_date_filter_metadata(start_date, end_date),
        "sample_full_records_returned": len(rows),
        "sample_full_records": [clean_full_row(row) for row in rows]
    }


@mcp.tool()
def search_mysql_any_value_optimized(
    search_value: str,
    limit: int = 5,
    start_date=None,
    end_date=None
) -> dict:
    """
    Universal optimized search.
    Searches any user value across all MySQL dataset columns.
    Returns only important compact fields.
    Long text is trimmed to 200 characters.
    Full row is not returned unless requested separately.
    Optionally filter records by call_date.
    """

    search_value = str(search_value).strip()
    columns = get_all_columns()

    if not search_value:
        return {
            "error": "search_value cannot be empty"
        }

    if not columns:
        return {
            "error": "No columns found in MySQL table",
            "table": TABLE_NAME
        }

    compact_columns = [
        col for col in IMPORTANT_COLUMNS
        if col in columns
    ]

    if not compact_columns:
        compact_columns = columns[:8]

    where_clause = " OR ".join(
        [f"LOWER(CAST(`{column}` AS CHAR)) LIKE LOWER(%s)" for column in columns]
    )
    full_where_clause, date_params = build_where_clause(
        base_condition=where_clause,
        start_date=start_date,
        end_date=end_date
    )

    search_params = [f"%{search_value}%"] * len(columns)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        f"""
        SELECT COUNT(*) AS total_matches
        FROM `{TABLE_NAME}`
        {full_where_clause}
        """,
        search_params + date_params
    )

    total_matches = cursor.fetchone()["total_matches"]

    selected_columns = ", ".join([f"`{col}`" for col in compact_columns])

    cursor.execute(
        f"""
        SELECT {selected_columns}
        FROM `{TABLE_NAME}`
        {full_where_clause}
        LIMIT %s
        """,
        search_params + date_params + [limit]
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "searched_value": search_value,
        "total_matches": total_matches,
        "returned_records": len(rows),
        "returned_columns": compact_columns,
        "date_filter": get_date_filter_metadata(start_date, end_date),
        "optimization_used": [
            "universal_search_across_all_columns",
            "compact_columns_only",
            "200_character_text_trimming",
            "limited_result_count",
            "count_first_inside_search",
            "full_details_on_demand"
        ],
        "note": "Compact results are returned to reduce tokens and cost. Use full record tools for complete details.",
        "data": [clean_compact_row(row) for row in rows]
    }


@mcp.tool()
def get_mysql_full_call_by_id(
    id: int,
    start_date=None,
    end_date=None
) -> dict:
    """
    Fetch full dataset row only when needed using MySQL id.
    Optionally filter records by call_date.
    """

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    where_clause, date_params = build_where_clause(
        base_condition="`id` = %s",
        start_date=start_date,
        end_date=end_date
    )

    cursor.execute(
        f"""
        SELECT *
        FROM `{TABLE_NAME}`
        {where_clause}
        LIMIT 1
        """,
        [id] + date_params
    )

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row:
        return {
            "retrieval_type": "full_record",
            "note": "Full record returned without trimming.",
            "date_filter": get_date_filter_metadata(start_date, end_date),
            "data": clean_full_row(row)
        }

    return {
        "message": "No record found for this id",
        "date_filter": get_date_filter_metadata(start_date, end_date)
    }


@mcp.tool()
def get_mysql_full_call_by_recording_id(
    recording_id: str,
    start_date=None,
    end_date=None
) -> dict:
    """
    Fetch full dataset row only when needed using recording_id.
    Optionally filter records by call_date.
    """

    recording_id = str(recording_id).strip()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    where_clause, date_params = build_where_clause(
        base_condition="`recording_id` = %s",
        start_date=start_date,
        end_date=end_date
    )

    cursor.execute(
        f"""
        SELECT *
        FROM `{TABLE_NAME}`
        {where_clause}
        LIMIT 1
        """,
        [recording_id] + date_params
    )

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row:
        return {
            "retrieval_type": "full_record",
            "note": "Full record returned without trimming.",
            "date_filter": get_date_filter_metadata(start_date, end_date),
            "data": clean_full_row(row)
        }

    return {
        "message": "No record found for this recording_id",
        "date_filter": get_date_filter_metadata(start_date, end_date)
    }


@mcp.tool()
def get_all_issue_patterns(
    start_date=None,
    end_date=None,
    limit: int = 10
) -> dict:
    """
    Analyze recurring customer issues across compact call analytics fields.

    Example SQL shape:
    SELECT call_date, focus_areas, areas_of_improvement, call_summary,
           final_conclusion, negative_sentiment
    FROM calls
    WHERE call_date >= %s AND call_date <= %s
    """

    limit = safe_limit(limit)
    rows = fetch_analysis_rows(
        columns=[
            "call_date",
            "focus_areas",
            "areas_of_improvement",
            "call_summary",
            "final_conclusion",
            "negative_sentiment",
        ],
        start_date=start_date,
        end_date=end_date
    )

    result = build_issue_pattern_result(
        rows=rows,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )

    result["analysis_type"] = "all_issue_patterns"
    result["description"] = (
        "Grouped issue patterns from focus areas, improvement areas, "
        "call summaries, final conclusion, and negative sentiment."
    )

    return result


@mcp.tool()
def get_improvement_areas(
    start_date=None,
    end_date=None,
    limit: int = 10
) -> dict:
    """
    Identify repeated quality improvement areas across calls.

    Example SQL shape:
    SELECT areas_of_improvement, greeting, listening_skills, probing, closure
    FROM calls
    WHERE call_date >= %s AND call_date <= %s
    """

    limit = safe_limit(limit)
    rows = fetch_analysis_rows(
        columns=[
            "areas_of_improvement",
            "greeting",
            "listening_skills",
            "probing",
            "closure",
        ],
        start_date=start_date,
        end_date=end_date
    )

    improvement_counter = Counter()
    sample_counter = {}

    for row in rows:
        for item in parse_text_items(row.get("areas_of_improvement")):
            category = normalize_category(item, IMPROVEMENT_KEYWORDS)
            improvement_counter[category] += 1

            if category not in sample_counter:
                sample_counter[category] = shorten_text(item, 180)

        for metric in ["greeting", "listening_skills", "probing", "closure"]:
            try:
                score = float(row.get(metric) or 0)
            except (TypeError, ValueError):
                score = 0

            if 0 < score < 8:
                improvement_counter[metric] += 1

                if metric not in sample_counter:
                    sample_counter[metric] = (
                        f"{metric} score below target: {score}"
                    )

    grouped_improvements = []

    for index, (area, frequency) in enumerate(
        improvement_counter.most_common(limit),
        start=1
    ):
        grouped_improvements.append(
            {
                "rank": index,
                "improvement_area": area,
                "frequency": frequency,
                "sample_evidence": sample_counter.get(area, ""),
            }
        )

    return {
        "analysis_type": "improvement_areas",
        "date_filter": get_date_filter_metadata(start_date, end_date),
        "total_records_analyzed": len(rows),
        "grouped_improvement_categories": grouped_improvements,
    }


@mcp.tool()
def get_language_distribution(
    start_date=None,
    end_date=None,
    limit: int = 20
) -> dict:
    """
    Analyze total calls by language using GROUP BY language.

    Example SQL:
    SELECT language, COUNT(*) AS total_calls
    FROM calls
    WHERE call_date >= %s AND call_date <= %s
    GROUP BY language
    ORDER BY total_calls DESC
    """

    limit = safe_limit(limit, default=20)
    where_clause, date_params = build_where_clause(
        start_date=start_date,
        end_date=end_date
    )

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        f"""
        SELECT
            COALESCE(NULLIF(TRIM(`language`), ''), 'unknown') AS language,
            COUNT(*) AS total_calls
        FROM `{TABLE_NAME}`
        {where_clause}
        GROUP BY language
        ORDER BY total_calls DESC
        LIMIT %s
        """,
        date_params + [limit]
    )

    rows = cursor.fetchall()

    cursor.execute(
        f"""
        SELECT COUNT(*) AS total_records
        FROM `{TABLE_NAME}`
        {where_clause}
        """,
        date_params
    )
    total_records = cursor.fetchone()["total_records"]

    cursor.close()
    conn.close()

    return {
        "analysis_type": "language_distribution",
        "date_filter": get_date_filter_metadata(start_date, end_date),
        "total_records_analyzed": total_records,
        "returned_languages": len(rows),
        "data": rows,
    }


@mcp.tool()
def get_top_products_discussed(
    start_date=None,
    end_date=None,
    limit: int = 10
) -> dict:
    """
    Find the most discussed products from products_discussed.

    Example SQL shape:
    SELECT products_discussed
    FROM calls
    WHERE call_date >= %s AND call_date <= %s
    """

    limit = safe_limit(limit)
    rows = fetch_analysis_rows(
        columns=["products_discussed"],
        start_date=start_date,
        end_date=end_date
    )

    product_counter = Counter()

    for row in rows:
        for product in parse_text_items(row.get("products_discussed")):
            product = product.lower().strip()

            if product:
                product_counter[product] += 1

    return {
        "analysis_type": "top_products_discussed",
        "date_filter": get_date_filter_metadata(start_date, end_date),
        "total_records_analyzed": len(rows),
        "returned_products": min(len(product_counter), limit),
        "data": format_counter(product_counter, limit),
    }


@mcp.tool()
def get_repeated_issue_patterns(
    start_date=None,
    end_date=None,
    limit: int = 10,
    minimum_frequency: int = 3
) -> dict:
    """
    Detect high-frequency recurring customer issues.

    This is stricter than get_all_issue_patterns because it only returns
    issue categories that meet minimum_frequency.
    """

    limit = safe_limit(limit)
    minimum_frequency = safe_limit(
        minimum_frequency,
        default=3,
        maximum=100
    )
    rows = fetch_analysis_rows(
        columns=[
            "call_date",
            "focus_areas",
            "areas_of_improvement",
            "call_summary",
            "final_conclusion",
            "negative_sentiment",
        ],
        start_date=start_date,
        end_date=end_date
    )

    result = build_issue_pattern_result(
        rows=rows,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        minimum_frequency=minimum_frequency
    )

    result["analysis_type"] = "repeated_issue_patterns"
    result["minimum_frequency"] = minimum_frequency
    result["description"] = (
        "High-frequency recurring issue categories only."
    )

    return result


if __name__ == "__main__":
    mcp.run()
