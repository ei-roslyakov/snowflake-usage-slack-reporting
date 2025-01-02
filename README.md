# Snowflake Usage to Slack Reporting Tool

This Python script automates the process of retrieving usage data from Snowflake, formatting it into a readable table, and sending it to specified Slack channels. It provides an efficient way for teams to track and manage resource usage over time.

## Features

- **Data Retrieval**: Fetches usage data from Snowflake using customizable SQL queries.
- **Data Formatting**: Creates clear and concise tables using `tabulate` and `AsciiTable`.
- **Slack Integration**: Sends formatted tables and summary messages directly to Slack channels.

## Prerequisites

Before running the script, ensure you have the following:

- **Python**: Version 3.6 or higher.
- **Required Packages**: Install the following Python libraries:
  - `requests`
  - `snowflake-connector-python`
  - `python-dotenv`
  - `tabulate`
  - `terminaltables`
  - `loguru`
- **Snowflake Account**: With the necessary permissions to access usage data.
- **Slack Bot**: With posting permissions and a valid token.

## Installation

1. Clone this repository or download the script directly.

2. Install the required Python packages:

   ```bash
   pip install requests snowflake-connector-python python-dotenv tabulate terminaltables loguru
   ```

3. Set up your environment variables in a `.env` file:

   ```plaintext
   SNOWFLAKE_ACCOUNT=<your_account>
   SNOWFLAKE_WAREHOUSE=<your_warehouse>
   SNOWFLAKE_DATABASE=<your_database>
   SNOWFLAKE_SCHEMA=<your_schema>
   SLACK_CHANNELS=<your_slack_channels_json_array>
   ```

4. Fill in the `.env.example` file with your credentials as follows:

   ```plaintext
   SNOWFLAKE_ACCOUNT = 'personal'
   SNOWFLAKE_USER = 'username'
   SNOWFLAKE_PASSWORD = 'password'
   SNOWFLAKE_WAREHOUSE = 'COMPUTE_WH'
   SNOWFLAKE_DATABASE = 'DEMO_DB'
   SNOWFLAKE_SCHEMA = 'PUBLIC'
   SLACK_TOKEN = "slack_token"
   SLACK_CHANNELS = ["general"]
   ```

   For local runs, rename `.env.example` to `.env` and ensure the environment variables are loaded.

   For Kubernetes deployments, use secrets to securely store these values.

5. Create a Kubernetes secret for sensitive data (if using Kubernetes):

   ```bash
   kubectl create secret generic snowflake-costs-alert \
       --from-literal=SNOWFLAKE_USER='username' \
       --from-literal=SNOWFLAKE_PASSWORD='<your_password>' \
       --from-literal=SLACK_TOKEN='<your_slack_token>' \
       -n monitoring --dry-run=client -o yaml | kubectl apply -f -
   ```

6. Build the Docker image:

   ```bash
   docker build -t snowflake-usage-slack-reporting:latest .
   ```

## Usage

### Local Execution

Run the script locally using:

```bash
python app.py
```

### Kubernetes Deployment

1. Ensure the Kubernetes secret is created as shown in the Installation step.

2. Push the Docker image to a container registry (e.g., Docker Hub or AWS ECR):

   ```bash
   docker tag snowflake-usage-slack-reporting:latest <your_registry>/snowflake-usage-slack-reporting:latest
   docker push <your_registry>/snowflake-usage-slack-reporting:latest
   ```

3. Update the image reference in the `job.yaml` file to point to the pushed image:

   ```yaml
   containers:
   - name: report-generator
     image: <your_registry>/snowflake-usage-slack-reporting:latest
   ```

4. Deploy the CronJob to Kubernetes:

   ```bash
   kubectl apply -f job.yaml
   ```

## Kubernetes CronJob Configuration

The included CronJob YAML runs the script on a weekly schedule. Modify the `schedule` field in the `CronJob` specification to adjust the timing. For example:

```yaml
schedule: "19 14 * * 1"  # Runs every Monday at 14:19 UTC
```

## Environment Variables

- **`SNOWFLAKE_ACCOUNT`**: Your Snowflake account identifier.
- **`SNOWFLAKE_USER`**: Username for Snowflake.
- **`SNOWFLAKE_PASSWORD`**: Password for Snowflake.
- **`SNOWFLAKE_WAREHOUSE`**: Warehouse name in Snowflake.
- **`SNOWFLAKE_DATABASE`**: Database name in Snowflake.
- **`SNOWFLAKE_SCHEMA`**: Schema name in Snowflake.
- **`SLACK_TOKEN`**: Slack bot token for authentication.
- **`SLACK_CHANNELS`**: JSON array of Slack channel IDs.

## Troubleshooting

- **Environment Variables Not Set**: Ensure all required variables are defined in your `.env` file or Kubernetes secret.
- **Slack Errors**: Verify the Slack bot has appropriate permissions and the `SLACK_TOKEN` is correct.
- **Snowflake Connection Issues**: Check Snowflake credentials and account configuration.
