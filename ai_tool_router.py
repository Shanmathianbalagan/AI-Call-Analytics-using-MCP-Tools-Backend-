import json
import logging
from json import JSONDecodeError

from dotenv import load_dotenv
from openai import OpenAI

from mysql_mcp_server import (
    get_all_issue_patterns,
    get_improvement_areas,
    get_language_distribution,
    get_mysql_dataset_summary,
    get_mysql_full_call_by_id,
    get_mysql_full_call_by_recording_id,
    get_repeated_issue_patterns,
    get_top_products_discussed,
    search_mysql_any_value_optimized,
)


load_dotenv()

client = OpenAI()
logging.getLogger("httpx").setLevel(logging.WARNING)

ALLOWED_TOOLS = {
    "normal_chat",
    "get_all_issue_patterns",
    "get_improvement_areas",
    "get_language_distribution",
    "get_mysql_dataset_summary",
    "search_mysql_any_value_optimized",
    "get_mysql_full_call_by_id",
    "get_mysql_full_call_by_recording_id",
    "get_repeated_issue_patterns",
    "get_top_products_discussed",
}


SYSTEM_PROMPT = """
You are an AI tool router.

Your job is to choose exactly one tool for the user's query.

Allowed tools:

1. normal_chat
Use for greetings, thanks, casual messages, or questions that do not need MySQL.

2. get_mysql_dataset_summary
Use when the user asks about dataset summary, total records, table columns,
or sample records.
Optional date arguments:
- start_date: YYYY-MM-DD
- end_date: YYYY-MM-DD

3. search_mysql_any_value_optimized
Use when the user searches for calls by keyword, product, language, gender,
pricing, sentiment, offer, topic, or any general value.
Arguments:
- search_value: string
- limit: integer, default 5
Optional date arguments:
- start_date: YYYY-MM-DD
- end_date: YYYY-MM-DD

4. get_mysql_full_call_by_id
Use when the user asks for full details using a numeric MySQL id.
Arguments:
- id: integer
Optional date arguments:
- start_date: YYYY-MM-DD
- end_date: YYYY-MM-DD

5. get_mysql_full_call_by_recording_id
Use when the user asks for full details using recording_id.
Arguments:
- recording_id: string
Optional date arguments:
- start_date: YYYY-MM-DD
- end_date: YYYY-MM-DD

6. get_all_issue_patterns
Use when the user asks for all issue patterns, complaints, customer pain
points, customer problems, or major issues in the dataset.
Arguments:
- limit: integer, default 10
Optional date arguments:
- start_date: YYYY-MM-DD
- end_date: YYYY-MM-DD

7. get_improvement_areas
Use when the user asks for improvement areas, top weaknesses, support gaps,
quality improvement analysis, or repeated quality issues.
Arguments:
- limit: integer, default 10
Optional date arguments:
- start_date: YYYY-MM-DD
- end_date: YYYY-MM-DD

8. get_language_distribution
Use when the user asks for language distribution, calls by language, or
comparison between languages.
Arguments:
- limit: integer, default 20
Optional date arguments:
- start_date: YYYY-MM-DD
- end_date: YYYY-MM-DD

9. get_top_products_discussed
Use when the user asks for top products, most discussed products, popular
products, or product frequency.
Arguments:
- limit: integer, default 10
Optional date arguments:
- start_date: YYYY-MM-DD
- end_date: YYYY-MM-DD

10. get_repeated_issue_patterns
Use when the user asks for repeated issues, recurring complaints, repeated
customer frustrations, or high-frequency complaints.
Arguments:
- limit: integer, default 10
- minimum_frequency: integer, default 3
Optional date arguments:
- start_date: YYYY-MM-DD
- end_date: YYYY-MM-DD

Date extraction rules:
- Current date is 2026-06-15.
- If the user gives exact dates, use those dates.
- "today" means start_date 2026-06-15 and end_date 2026-06-15.
- "yesterday" means start_date 2026-06-14 and end_date 2026-06-14.
- "past one week" or "last 7 days" means start_date 2026-06-08
  and end_date 2026-06-15.
- "last week" means start_date 2026-06-08 and end_date 2026-06-14.
- "this month" means start_date 2026-06-01 and end_date 2026-06-15.
- If no date range is mentioned, do not include start_date or end_date.

Return only valid JSON in this exact format:
{
  "tool": "tool_name",
  "arguments": {}
}

Do not explain.
Do not answer the user directly.
Do not include markdown.
"""

FINAL_RESPONSE_PROMPT = """
You are a helpful assistant for a call analytics dataset.

Your job is to format the provided MCP/MySQL tool result into a clear final
answer for the user.

Rules:
- Use only the provided tool result.
- Do not invent data.
- Do not claim you searched the database yourself.
- If the tool result says no record was found, say that clearly.
- Keep the answer concise and easy to read.
- For search results, mention total matches and summarize returned records.
- For full record results, summarize the important fields.
- For analytics results, summarize trends, rankings, frequencies, and date
  filter scope when provided.
- For normal chat, reply naturally and offer help with the call dataset.
"""


def decide_tool(user_query: str) -> dict:
    """Ask GPT-4o-mini to choose the correct MCP tool."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_query,
                },
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        decision = json.loads(content)
    except JSONDecodeError as error:
        return {
            "tool": "normal_chat",
            "arguments": {},
            "error": f"AI returned invalid JSON: {error}",
        }
    except Exception as error:
        return {
            "tool": "normal_chat",
            "arguments": {},
            "error": f"Tool decision failed: {error}",
        }

    if decision.get("tool") not in ALLOWED_TOOLS:
        return {
            "tool": "normal_chat",
            "arguments": {},
            "error": "AI selected an unsupported tool",
            "raw_decision": decision,
        }

    return decision


def execute_tool(decision: dict) -> dict:
    """Execute the MCP/MySQL tool selected by the AI router."""
    tool_name = decision.get("tool")
    arguments = decision.get("arguments", {})

    if not isinstance(arguments, dict):
        return {
            "error": "Tool arguments must be a JSON object.",
            "tool": tool_name,
            "arguments": arguments,
        }

    if decision.get("error"):
        return {
            "message": "No MCP/MySQL tool executed because routing failed.",
            "routing_error": decision["error"],
        }

    if tool_name == "normal_chat":
        return {
            "message": "Normal chat selected. No MySQL tool executed."
        }

    try:
        if tool_name == "get_mysql_dataset_summary":
            return get_mysql_dataset_summary(**arguments)

        if tool_name == "get_all_issue_patterns":
            return get_all_issue_patterns(**arguments)

        if tool_name == "get_improvement_areas":
            return get_improvement_areas(**arguments)

        if tool_name == "get_language_distribution":
            return get_language_distribution(**arguments)

        if tool_name == "search_mysql_any_value_optimized":
            return search_mysql_any_value_optimized(**arguments)

        if tool_name == "get_mysql_full_call_by_id":
            return get_mysql_full_call_by_id(**arguments)

        if tool_name == "get_mysql_full_call_by_recording_id":
            return get_mysql_full_call_by_recording_id(**arguments)

        if tool_name == "get_repeated_issue_patterns":
            return get_repeated_issue_patterns(**arguments)

        if tool_name == "get_top_products_discussed":
            return get_top_products_discussed(**arguments)
    except TypeError as error:
        return {
            "error": f"Tool received invalid arguments: {error}",
            "tool": tool_name,
            "arguments": arguments,
        }
    except Exception as error:
        return {
            "error": f"Tool execution failed: {error}",
            "tool": tool_name,
            "arguments": arguments,
        }

    return {
        "error": "Unsupported tool. Nothing was executed.",
        "tool": tool_name,
        "arguments": arguments,
    }


def format_final_response(
    user_query: str,
    decision: dict,
    tool_result: dict,
) -> str:
    """Ask GPT-4o-mini to format the tool result for the user."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": FINAL_RESPONSE_PROMPT,
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "user_query": user_query,
                            "tool_decision": decision,
                            "tool_result": tool_result,
                        },
                        default=str,
                    ),
                },
            ],
            temperature=0.2,
        )
    except Exception as error:
        return (
            "I could fetch the tool result, but final response formatting "
            f"failed: {error}"
        )

    return response.choices[0].message.content.strip()


def main() -> None:
    """Run the router in terminal mode."""
    print("MCP AI Tool Router")
    print("Type 'exit' to stop.\n")

    while True:
        user_query = input("User: ").strip()

        if user_query.lower() in {"exit", "quit"}:
            break

        decision = decide_tool(user_query)
        tool_result = execute_tool(decision)
        final_answer = format_final_response(
            user_query=user_query,
            decision=decision,
            tool_result=tool_result,
        )

        print("\nAI Tool Decision:")
        print(json.dumps(decision, indent=2))

        print("\nTool Result:")
        print(json.dumps(tool_result, indent=2, default=str))

        print("\nFinal Answer:")
        print(final_answer)
        print()


if __name__ == "__main__":
    main()
