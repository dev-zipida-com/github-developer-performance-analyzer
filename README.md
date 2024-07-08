# GitHub Developer Performance Analyzer

This script analyzes developer performance and calculates contribution scores for GitHub repositories.

## Features

- Collects commit, pull request, and issue data from multiple repositories
- Calculates performance metrics for each developer (commit count, code churn, PR count, etc.)
- Computes a contribution score for each developer
- Outputs results to a CSV file

## Requirements

- Python 3.6+
- Required Python packages: `PyGithub`, `pandas`, `python-dotenv`

## Installation

1. Clone this repository:

   ```
   git clone https://github.com/dev-zipida-com/github-developer-performance-analyzer.git
   ```

2. Install the required packages:

   ```
   pip install -r requirements.txt
   ```

## Usage

1. Create a `.env` file and set the following variables:

   ```
   GITHUB_ACCESS_TOKEN=your_github_access_token
   REPO_LIST=owner/repo1,owner/repo2
   START_DATE = 2023-07-01
   END_DATE = 2024-07-01
   FILEPATH=developer_performance.csv
   ```

2. Run the script:

   ```
   python main.py
   ```

3. Results will be saved in the specified CSV file.

## Contribution Score Calculation

The contribution score is calculated considering the following factors:

- Commit count (30%)
- Code churn (20%)
- PR count (20%)
- Merged PR rate (15%)
- Issue closure rate (15%)

Each factor is normalized and converted to a score between 0-100.

## Notes

- This tool uses quantitative metrics only and does not consider qualitative factors such as code quality or collaboration skills.
- Be mindful of GitHub API usage limits.
- Analysis of large repositories or long time periods may take considerable time to execute.
