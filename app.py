import os

import json
import loguru
import requests
import snowflake.connector
from dotenv import load_dotenv
from tabulate import tabulate
from terminaltables import AsciiTable

load_dotenv()


logger = loguru.logger
load_dotenv()


def get_env_variable(variable_name):
    value = os.environ.get(variable_name)
    if not value:
        logger.error(f"Environment variable {variable_name} is not set.")
        return None
    return value


def print_variables():
    for name, value in os.environ.items():
        logger.info(f"{name}: {value}")


SNOWFLAKE_ACCOUNT = get_env_variable("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = get_env_variable("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = get_env_variable("SNOWFLAKE_PASSWORD")
SNOWFLAKE_WAREHOUSE = get_env_variable("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_DATABASE = get_env_variable("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = get_env_variable("SNOWFLAKE_SCHEMA")
SLACK_TOKEN = get_env_variable("SLACK_TOKEN")
SLACK_CHANNELS = get_env_variable("SLACK_CHANNELS")


def get_data(sql_query):
    conn = snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        account=SNOWFLAKE_ACCOUNT,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
    )

    cur = conn.cursor()
    cur.execute(sql_query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def print_table(dict_list):
    if not dict_list:
        print("No data available to display.")
        return

    headers = list(dict_list[0].keys())
    table_data = [headers]

    for item in dict_list:
        row = [item.get(header, "") for header in headers]
        table_data.append(row)

    table = AsciiTable(table_data)

    print(table.table)


def order_data(data):
    dict_list = []
    for entry in data:
        dict_entry = {
            "Account Name": entry[0],
            entry[2]: f"{float(entry[1]):.2f}",
            entry[4]: f"{float(entry[3]):.2f}",
        }
        dict_list.append(dict_entry)

    return dict_list


def send_message_to_slack(channel, table_text, summary_message):
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {SLACK_TOKEN}",
        "Content-type": "application/json",
    }
    data = {
        "channel": f"{channel}",
        "text": f"```\n{table_text}\n\n{summary_message}```",
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        logger.info("Message sent successfully")
        logger.info(f"Response: {response.text}")
    else:
        logger.error(f"Failed to send message, status code: {response.text}")


def create_summary_message(data):
    messages = []
    for entry in data:
        account_name = entry["Account Name"]
        date_keys = [key for key in entry.keys() if key != "Account Name"]
        date_keys.sort()

        if len(date_keys) < 2:
            continue

        last_by_one_week = float(entry[date_keys[-2]])  # Second last item
        last_week = float(entry[date_keys[-1]])  # Last item

        if last_by_one_week == 0:
            continue
        percentage_diff = ((last_week - last_by_one_week) / last_by_one_week) * 100

        if percentage_diff > 0:
            messages.append(
                f"The usage for {account_name} last week was {abs(percentage_diff):.2f}% higher than the week before."
            )
        else:
            messages.append(
                f"The usage for {account_name} last week was {abs(percentage_diff):.2f}% lower than the week before."
            )

    return "\n".join(messages)


def main():
    print_variables()

    sql_query = """  # noqa
        SELECT account_name,
            ROUND(SUM(CASE WHEN usage_date BETWEEN DATEADD(week, -2, CURRENT_DATE) AND DATEADD(day, -1, DATEADD(week, -1, CURRENT_DATE)) THEN usage_in_currency ELSE 0 END), 2) AS usage_last_by_one_week,
            TO_CHAR(DATEADD(week, -2, CURRENT_DATE), 'YYYY-MM-DD') || ' to ' || TO_CHAR(DATEADD(day, -1, DATEADD(week, -1, CURRENT_DATE)), 'YYYY-MM-DD') AS date_range_last_by_one_week,
            ROUND(SUM(CASE WHEN usage_date BETWEEN DATEADD(week, -1, CURRENT_DATE) AND DATEADD(day, -1, CURRENT_DATE) THEN usage_in_currency ELSE 0 END), 2) AS usage_last_week,
            TO_CHAR(DATEADD(week, -1, CURRENT_DATE), 'YYYY-MM-DD') || ' to ' || TO_CHAR(DATEADD(day, -1, CURRENT_DATE), 'YYYY-MM-DD') AS date_range_last_week
        FROM snowflake.organization_usage.usage_in_currency_daily
        WHERE usage_date BETWEEN DATEADD(week, -2, CURRENT_DATE) AND DATEADD(day, -1, CURRENT_DATE)
        GROUP BY 1
        ORDER BY 2 DESC, 4 DESC;
    """

    logger.info("Getting data from Snowflake...")
    data = get_data(sql_query)
    logger.info("Data received.")
    logger.info("Ordering data...")
    data = order_data(data)
    logger.info(f"Data: {data}")
    if data != "[]":
        output_string = tabulate(
            [
                {
                    k: ("$" + v if isinstance(v, str) and k != "Account Name" else v)
                    for k, v in d.items()
                }
                for d in data
            ],
            headers="keys",
            tablefmt="orgtbl",
        )
        summary_message = create_summary_message(data)

        logger.info("Sending the table to Slack...")

        for channel in json.loads(SLACK_CHANNELS):
            logger.info(f"Sending the table to Slack channel: {channel}...")
            send_message_to_slack(channel, output_string, summary_message)
            logger.info(f"Data sent to Slack for the {channel}")
        print_table(
            [
                {
                    k: ("$" + v if isinstance(v, str) and k != "Account Name" else v)
                    for k, v in d.items()
                }
                for d in data
            ]
        )
    else:
        logger.info("No data to send to Slack.")


if __name__ == "__main__":
    logger.info("Application started")
    main()
    logger.info("Application finished")
