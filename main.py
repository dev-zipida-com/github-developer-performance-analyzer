import os
from github import Github
from collections import defaultdict
from datetime import datetime, timedelta
from pytz import UTC
from dotenv import load_dotenv 
import pandas as pd

# env
load_dotenv(override=True)

GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
REPO_LIST = os.getenv("REPO_LIST").split(",")
WORKING_DAYS = int(os.getenv("WORKING_DAYS"))
FILEPATH = os.getenv("FILEPATH")

def analyze_developer_performance(repos):
    performance_data = defaultdict(lambda: defaultdict(int))
    commit_times = defaultdict(lambda: {"first": None, "last": None})

    for repo_name in repos:
        repo = g.get_repo(repo_name)
        
        # 모든 브랜치 가져오기
        branches = repo.get_branches()

        # 각 브랜치에 대해 커밋 분석
        for branch in branches:
            try:
                commits = repo.get_commits(sha=branch.name, since=start_date, until=end_date)
                for commit in commits:
                    author = commit.author.login if commit.author else "Unknown"
                    commit_time = commit.commit.author.date.replace(tzinfo=UTC)
                    
                    performance_data[author]["commit_count"] += 1
                    performance_data[author]["lines_added"] += commit.stats.additions
                    performance_data[author]["lines_deleted"] += commit.stats.deletions

                    # 첫 번째와 마지막 커밋 시간 업데이트
                    if commit_times[author]["first"] is None or commit_time < commit_times[author]["first"]:
                        commit_times[author]["first"] = commit_time
                    if commit_times[author]["last"] is None or commit_time > commit_times[author]["last"]:
                        commit_times[author]["last"] = commit_time

            except Exception as e:
                print(f"Error getting commits for branch {branch.name}: {str(e)}")

        # PR 분석 (변경 없음)
        prs = repo.get_pulls(state='all', sort='created', direction='desc')
        for pr in prs:
            if start_date <= pr.created_at <= end_date:
                author = pr.user.login
                performance_data[author]["pr_count"] += 1
                if pr.merged:
                    performance_data[author]["merged_pr_count"] += 1

        # 이슈 분석 (변경 없음)
        issues = repo.get_issues(state='all', sort='created', direction='desc')
        for issue in issues:
            if start_date <= issue.created_at <= end_date:
                if issue.assignee:
                    assignee_login = issue.assignee.login
                    performance_data[assignee_login]["assigned_issues"] += 1
                    if issue.state == 'closed':
                        performance_data[assignee_login]["closed_issues"] += 1
                else:
                    performance_data["Unassigned"]["assigned_issues"] += 1
                    if issue.state == 'closed':
                        performance_data["Unassigned"]["closed_issues"] += 1

    # 첫 번째와 마지막 커밋 시간을 performance_data에 추가
    for author, times in commit_times.items():
        performance_data[author]["first_commit"] = times["first"]
        performance_data[author]["last_commit"] = times["last"]

    return performance_data

# 기여도 점수 계산 함수
# 커밋 수 (30%): 개발자의 지속적인 기여를 나타냅니다. 가장 많은 커밋을 한 개발자를 기준으로 정규화합니다.
# 코드 변경량 (20%): 추가 및 삭제된 라인 수의 합계로, 개발자가 얼마나 많은 코드를 작성하고 수정했는지를 나타냅니다. 마찬가지로 최대값을 기준으로 정규화합니다.
# PR 수 (20%): 개발자가 얼마나 많은 기능이나 수정사항을 제안했는지를 나타냅니다. 최대값을 기준으로 정규화합니다.
# 병합된 PR 비율 (15%): 개발자가 제안한 변경사항의 품질을 간접적으로 나타냅니다. 이미 0-1 사이의 값이므로 정규화가 필요 없습니다.
# 해결한 이슈 비율 (15%): 개발자가 할당받은 작업을 얼마나 잘 완료했는지를 나타냅니다. 이 역시 0-1 사이의 값입니다.
def calculate_contribution_score(row):
    commit_score = row['commit_count'] / df['commit_count'].max() if df['commit_count'].max() > 0 else 0
    churn_score = row['code_churn'] / df['code_churn'].max() if df['code_churn'].max() > 0 else 0
    pr_score = row['pr_count'] / df['pr_count'].max() if df['pr_count'].max() > 0 else 0
    pr_merge_score = row['pr_merge_rate']
    issue_close_score = row['issue_close_rate']
    
    total_score = (
        commit_score * 0.3 +
        churn_score * 0.2 +
        pr_score * 0.2 +
        pr_merge_score * 0.15 +
        issue_close_score * 0.15
    )
    
    return total_score * 100  # 백분율로 변환

if __name__ == '__main__':
  # GitHub 액세스 토큰
  g = Github(GITHUB_ACCESS_TOKEN)

  # 분석할 레포지토리 리스트
  repos = REPO_LIST

  # 분석 기간 설정 (예: 최근 3개월)
  end_date = datetime.now(UTC)
  start_date = (end_date - timedelta(days=WORKING_DAYS)).replace(tzinfo=UTC)

  # 성과 데이터 수집
  performance_data = analyze_developer_performance(repos)

  # 데이터프레임으로 변환
  df = pd.DataFrame.from_dict(performance_data, orient='index')

  # 누락된 열을 0으로 초기화
  for col in ['commit_count', 'lines_added', 'lines_deleted', 'pr_count', 'merged_pr_count', 'assigned_issues', 'closed_issues']:
      if col not in df.columns:
          df[col] = 0

  # 추가 지표 계산
  df['code_churn'] = df['lines_added'] + df['lines_deleted']
  df['pr_merge_rate'] = df['merged_pr_count'].div(df['pr_count'].where(df['pr_count'] != 0, 1))
  df['issue_close_rate'] = df['closed_issues'].div(df['assigned_issues'].where(df['assigned_issues'] != 0, 1))

  # NaN 값을 0으로 대체 (datetime 열 제외)
  df = df.fillna({col: 0 for col in df.columns if col not in ['first_commit', 'last_commit']})

  # 기여도 점수 계산 및 추가
  df['contribution_score'] = df.apply(calculate_contribution_score, axis=1)

  # 결과 출력
  print(df)

  # CSV 파일로 저장
  df.to_csv(FILEPATH)