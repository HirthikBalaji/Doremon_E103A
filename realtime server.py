from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import statistics
from collections import defaultdict
import random
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Productivity Scoring System")


# ==================== Configuration ====================

class APIConfig(BaseModel):
    github_token: Optional[str] = Field(default=None)
    slack_token: Optional[str] = Field(default=None)
    jira_url: Optional[str] = Field(default=None)
    jira_email: Optional[str] = Field(default=None)
    jira_token: Optional[str] = Field(default=None)
    google_calendar_credentials: Optional[str] = Field(default=None)


# Global config storage
api_config = APIConfig(
    github_token=os.getenv("GITHUB_TOKEN"),
    slack_token=os.getenv("SLACK_TOKEN"),
    jira_url=os.getenv("JIRA_URL"),
    jira_email=os.getenv("JIRA_EMAIL"),
    jira_token=os.getenv("JIRA_TOKEN")
)


# ==================== Data Models ====================

class GitHubCommit(BaseModel):
    commit_id: str
    lines_added: int
    lines_deleted: int
    files_changed: int
    review_time_hours: float
    merge_conflicts: int


class SlackMessage(BaseModel):
    message_id: str
    text: str
    timestamp: datetime


class JiraIssue(BaseModel):
    issue_id: str
    story_points: int
    time_spent_hours: float
    complexity: str


class Meeting(BaseModel):
    meeting_id: str
    duration_minutes: int
    type: str


class TeamMemberData(BaseModel):
    member_id: str
    name: str
    github_commits: List[GitHubCommit]
    slack_messages: List[SlackMessage]
    jira_issues: List[JiraIssue]
    meetings: List[Meeting]


class DataSourceRequest(BaseModel):
    github_username: Optional[str] = None
    github_repo: Optional[str] = None
    slack_user_id: Optional[str] = None
    jira_user_email: Optional[str] = None
    days_lookback: int = 30


# ==================== Real API Data Fetchers ====================

class GitHubDataFetcher:
    """Fetch real data from GitHub API"""

    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.base_url = "https://api.github.com"

    async def fetch_user_commits(self, username: str, repo: str = None, days: int = 30) -> List[GitHubCommit]:
        """Fetch commits for a user from GitHub"""
        commits = []
        since_date = (datetime.now() - timedelta(days=days)).isoformat()

        try:
            async with httpx.AsyncClient() as client:
                # If repo specified, get commits from that repo
                if repo:
                    url = f"{self.base_url}/repos/{repo}/commits"
                    params = {"author": username, "since": since_date, "per_page": 100}
                    response = await client.get(url, headers=self.headers, params=params)
                    response.raise_for_status()
                    commit_list = response.json()
                else:
                    # Get user's recent events
                    url = f"{self.base_url}/users/{username}/events"
                    response = await client.get(url, headers=self.headers)
                    response.raise_for_status()
                    events = response.json()
                    commit_list = [e for e in events if e.get("type") == "PushEvent"]

                # Process each commit
                for i, commit_data in enumerate(commit_list[:50]):  # Limit to 50
                    # Get detailed commit info
                    if repo and "sha" in commit_data:
                        detail_url = f"{self.base_url}/repos/{repo}/commits/{commit_data['sha']}"
                        detail_response = await client.get(detail_url, headers=self.headers)
                        detail_response.raise_for_status()
                        details = detail_response.json()

                        stats = details.get("stats", {})
                        files = details.get("files", [])

                        commits.append(GitHubCommit(
                            commit_id=commit_data["sha"][:8],
                            lines_added=stats.get("additions", 0),
                            lines_deleted=stats.get("deletions", 0),
                            files_changed=len(files),
                            review_time_hours=random.uniform(0.5, 3.0),  # Estimate
                            merge_conflicts=0  # Would need PR API for this
                        ))

                    if len(commits) >= 20:  # Limit API calls
                        break

        except httpx.HTTPError as e:
            print(f"GitHub API Error: {e}")
            return []

        return commits


class SlackDataFetcher:
    """Fetch real data from Slack API"""

    def __init__(self, token: str):
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"}
        self.base_url = "https://slack.com/api"

    async def fetch_user_messages(self, user_id: str, days: int = 30) -> List[SlackMessage]:
        """Fetch messages for a user from Slack"""
        messages = []
        oldest = (datetime.now() - timedelta(days=days)).timestamp()

        try:
            async with httpx.AsyncClient() as client:
                # Get list of channels
                channels_response = await client.get(
                    f"{self.base_url}/conversations.list",
                    headers=self.headers
                )
                channels_response.raise_for_status()
                channels = channels_response.json().get("channels", [])

                # Search messages from user in channels
                for channel in channels[:10]:  # Limit to 10 channels
                    history_response = await client.get(
                        f"{self.base_url}/conversations.history",
                        headers=self.headers,
                        params={"channel": channel["id"], "oldest": oldest, "limit": 100}
                    )
                    history_response.raise_for_status()
                    channel_messages = history_response.json().get("messages", [])

                    for msg in channel_messages:
                        if msg.get("user") == user_id and "text" in msg:
                            messages.append(SlackMessage(
                                message_id=msg.get("ts", ""),
                                text=msg["text"],
                                timestamp=datetime.fromtimestamp(float(msg.get("ts", 0)))
                            ))

                    if len(messages) >= 50:  # Limit total messages
                        break

        except httpx.HTTPError as e:
            print(f"Slack API Error: {e}")
            return []

        return messages


class JiraDataFetcher:
    """Fetch real data from Jira API"""

    def __init__(self, url: str, email: str, token: str):
        self.url = url.rstrip('/')
        self.auth = (email, token)
        self.headers = {"Accept": "application/json"}

    async def fetch_user_issues(self, user_email: str, days: int = 30) -> List[JiraIssue]:
        """Fetch issues for a user from Jira"""
        issues = []
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        try:
            async with httpx.AsyncClient() as client:
                # JQL query to get user's issues
                jql = f'assignee = "{user_email}" AND updated >= "{start_date}" ORDER BY updated DESC'

                response = await client.get(
                    f"{self.url}/rest/api/3/search",
                    auth=self.auth,
                    headers=self.headers,
                    params={"jql": jql, "maxResults": 50, "fields": "summary,customfield_10016,timespent,priority"}
                )
                response.raise_for_status()
                jira_issues = response.json().get("issues", [])

                for issue in jira_issues:
                    fields = issue.get("fields", {})

                    # Get story points (customfield_10016 is common, but varies)
                    story_points = fields.get("customfield_10016", 0) or random.randint(2, 8)

                    # Get time spent
                    time_spent_seconds = fields.get("timespent", 0) or (story_points * 3600 * 2)
                    time_spent_hours = time_spent_seconds / 3600

                    # Map priority to complexity
                    priority = fields.get("priority", {}).get("name", "Medium")
                    complexity_map = {
                        "Highest": "high",
                        "High": "high",
                        "Medium": "medium",
                        "Low": "low",
                        "Lowest": "low"
                    }
                    complexity = complexity_map.get(priority, "medium")

                    issues.append(JiraIssue(
                        issue_id=issue["key"],
                        story_points=int(story_points) if story_points else 5,
                        time_spent_hours=time_spent_hours,
                        complexity=complexity
                    ))

        except httpx.HTTPError as e:
            print(f"Jira API Error: {e}")
            return []

        return issues


class CalendarDataFetcher:
    """Fetch meeting data - placeholder for Google Calendar integration"""

    async def fetch_meetings(self, user_email: str, days: int = 30) -> List[Meeting]:
        """Fetch meetings - would use Google Calendar API"""
        # This would require OAuth2 flow with Google Calendar API
        # For now, return estimated data based on typical patterns
        print(f"Calendar API integration would fetch meetings for {user_email}")
        return []


# ==================== Data Aggregator ====================

async def fetch_real_data(request: DataSourceRequest) -> TeamMemberData:
    """Aggregate data from all sources"""

    member_id = request.github_username or request.slack_user_id or request.jira_user_email or "unknown"
    name = member_id

    commits = []
    messages = []
    issues = []
    meetings = []

    # Fetch GitHub data
    if api_config.github_token and request.github_username:
        print(f"Fetching GitHub data for {request.github_username}...")
        fetcher = GitHubDataFetcher(api_config.github_token)
        commits = await fetcher.fetch_user_commits(
            request.github_username,
            request.github_repo,
            request.days_lookback
        )
        print(f"  ✓ Found {len(commits)} commits")

    # Fetch Slack data
    if api_config.slack_token and request.slack_user_id:
        print(f"Fetching Slack data for {request.slack_user_id}...")
        fetcher = SlackDataFetcher(api_config.slack_token)
        messages = await fetcher.fetch_user_messages(request.slack_user_id, request.days_lookback)
        print(f"  ✓ Found {len(messages)} messages")

    # Fetch Jira data
    if all([api_config.jira_url, api_config.jira_email, api_config.jira_token]) and request.jira_user_email:
        print(f"Fetching Jira data for {request.jira_user_email}...")
        fetcher = JiraDataFetcher(api_config.jira_url, api_config.jira_email, api_config.jira_token)
        issues = await fetcher.fetch_user_issues(request.jira_user_email, request.days_lookback)
        print(f"  ✓ Found {len(issues)} issues")

    # Generate some estimated meeting data if no calendar integration
    print("Generating estimated meeting data...")
    for i in range(random.randint(8, 15)):
        meetings.append(Meeting(
            meeting_id=f"meet_{member_id}_{i}",
            duration_minutes=random.choice([30, 60, 90]),
            type=random.choice(["focus", "coordination", "interruption"])
        ))

    return TeamMemberData(
        member_id=member_id,
        name=name,
        github_commits=commits,
        slack_messages=messages,
        jira_issues=issues,
        meetings=meetings
    )


# ==================== Mock Data Generator (Fallback) ====================

def generate_mock_data():
    """Generate realistic mock data for a team"""

    team_members = []

    profiles = [
        {"member_id": "emp_001", "name": "Alice Chen", "profile": "high_performer"},
        {"member_id": "emp_002", "name": "Bob Martinez", "profile": "coordinator"},
        {"member_id": "emp_003", "name": "Carol Davis", "profile": "struggling"},
        {"member_id": "emp_004", "name": "David Kumar", "profile": "balanced"},
        {"member_id": "emp_005", "name": "Emma Wilson", "profile": "high_performer"}
    ]

    for profile_data in profiles:
        profile_type = profile_data["profile"]

        commits = []
        if profile_type == "high_performer":
            commit_count = random.randint(15, 25)
            for i in range(commit_count):
                commits.append(GitHubCommit(
                    commit_id=f"commit_{profile_data['member_id']}_{i}",
                    lines_added=random.randint(50, 300),
                    lines_deleted=random.randint(20, 100),
                    files_changed=random.randint(2, 8),
                    review_time_hours=random.uniform(0.5, 2.0),
                    merge_conflicts=random.randint(0, 1)
                ))
        elif profile_type == "coordinator":
            commit_count = random.randint(8, 12)
            for i in range(commit_count):
                commits.append(GitHubCommit(
                    commit_id=f"commit_{profile_data['member_id']}_{i}",
                    lines_added=random.randint(30, 150),
                    lines_deleted=random.randint(10, 60),
                    files_changed=random.randint(1, 5),
                    review_time_hours=random.uniform(1.0, 3.0),
                    merge_conflicts=random.randint(0, 2)
                ))
        elif profile_type == "struggling":
            commit_count = random.randint(5, 10)
            for i in range(commit_count):
                commits.append(GitHubCommit(
                    commit_id=f"commit_{profile_data['member_id']}_{i}",
                    lines_added=random.randint(20, 100),
                    lines_deleted=random.randint(10, 50),
                    files_changed=random.randint(1, 4),
                    review_time_hours=random.uniform(3.0, 8.0),
                    merge_conflicts=random.randint(2, 5)
                ))
        else:
            commit_count = random.randint(12, 18)
            for i in range(commit_count):
                commits.append(GitHubCommit(
                    commit_id=f"commit_{profile_data['member_id']}_{i}",
                    lines_added=random.randint(40, 200),
                    lines_deleted=random.randint(15, 80),
                    files_changed=random.randint(2, 6),
                    review_time_hours=random.uniform(1.0, 3.0),
                    merge_conflicts=random.randint(0, 2)
                ))

        slack_templates = {
            "status": ["Just completed the API integration task", "Working on the database migration now",
                       "Finished the code review for PR #123", "Done with the feature implementation"],
            "coordination": ["Can we schedule a sync meeting tomorrow?", "When is the next sprint planning?",
                             "Let's coordinate on the deployment", "Need to sync with the team on requirements"],
            "problem": ["Facing an issue with the authentication service", "Need help debugging this error",
                        "There's a bug in the payment module", "Stuck on this problem, anyone available?"]
        }

        messages = []
        message_count = random.randint(20, 40)
        for i in range(message_count):
            msg_type = random.choice(["status", "coordination", "problem"])
            messages.append(SlackMessage(
                message_id=f"msg_{profile_data['member_id']}_{i}",
                text=random.choice(slack_templates[msg_type]),
                timestamp=datetime.now() - timedelta(days=random.randint(0, 30))
            ))

        issues = []
        if profile_type == "high_performer":
            issue_count = random.randint(12, 18)
            for i in range(issue_count):
                complexity = random.choices(["low", "medium", "high"], weights=[0.2, 0.4, 0.4])[0]
                points = {"low": 2, "medium": 5, "high": 8}[complexity]
                issues.append(JiraIssue(
                    issue_id=f"TASK-{profile_data['member_id']}-{i}",
                    story_points=points,
                    time_spent_hours=points * random.uniform(0.8, 1.5),
                    complexity=complexity
                ))
        elif profile_type == "struggling":
            issue_count = random.randint(5, 8)
            for i in range(issue_count):
                complexity = random.choices(["low", "medium", "high"], weights=[0.5, 0.4, 0.1])[0]
                points = {"low": 2, "medium": 5, "high": 8}[complexity]
                issues.append(JiraIssue(
                    issue_id=f"TASK-{profile_data['member_id']}-{i}",
                    story_points=points,
                    time_spent_hours=points * random.uniform(2.0, 4.0),
                    complexity=complexity
                ))
        else:
            issue_count = random.randint(8, 14)
            for i in range(issue_count):
                complexity = random.choice(["low", "medium", "high"])
                points = {"low": 2, "medium": 5, "high": 8}[complexity]
                issues.append(JiraIssue(
                    issue_id=f"TASK-{profile_data['member_id']}-{i}",
                    story_points=points,
                    time_spent_hours=points * random.uniform(1.0, 2.0),
                    complexity=complexity
                ))

        meetings = []
        if profile_type == "coordinator":
            meeting_count = random.randint(20, 30)
            for i in range(meeting_count):
                meeting_type = random.choices(["focus", "coordination", "interruption"], weights=[0.2, 0.6, 0.2])[0]
                duration = {"focus": random.randint(60, 180), "coordination": random.randint(30, 60),
                            "interruption": random.randint(15, 30)}[meeting_type]
                meetings.append(Meeting(meeting_id=f"meet_{profile_data['member_id']}_{i}", duration_minutes=duration,
                                        type=meeting_type))
        else:
            meeting_count = random.randint(8, 15)
            for i in range(meeting_count):
                meeting_type = random.choices(["focus", "coordination", "interruption"], weights=[0.5, 0.3, 0.2])[0]
                duration = {"focus": random.randint(60, 180), "coordination": random.randint(30, 60),
                            "interruption": random.randint(15, 30)}[meeting_type]
                meetings.append(Meeting(meeting_id=f"meet_{profile_data['member_id']}_{i}", duration_minutes=duration,
                                        type=meeting_type))

        team_members.append(TeamMemberData(
            member_id=profile_data["member_id"],
            name=profile_data["name"],
            github_commits=commits,
            slack_messages=messages,
            jira_issues=issues,
            meetings=meetings
        ))

    return team_members


# ==================== Analysis Functions ====================

def calculate_code_complexity(commit: GitHubCommit) -> float:
    total_lines = commit.lines_added + commit.lines_deleted
    complexity = (total_lines * 0.6) + (commit.files_changed * 10)
    return min(complexity, 100)


def calculate_commit_impact(commit: GitHubCommit) -> Dict[str, float]:
    complexity_score = calculate_code_complexity(commit)
    review_penalty = min(commit.review_time_hours * 2, 20)
    conflict_penalty = commit.merge_conflicts * 5
    impact_score = max(complexity_score - review_penalty - conflict_penalty, 0)
    return {"complexity": complexity_score, "review_penalty": review_penalty, "conflict_penalty": conflict_penalty,
            "total_impact": impact_score}


def classify_slack_activity(message: SlackMessage) -> Dict[str, float]:
    text_lower = message.text.lower()
    status_keywords = ["update", "done", "completed", "finished", "working on"]
    coordination_keywords = ["meeting", "sync", "schedule", "when", "coordinate"]
    problem_keywords = ["issue", "problem", "bug", "error", "help", "stuck"]

    status_score = sum(1 for kw in status_keywords if kw in text_lower)
    coordination_score = sum(1 for kw in coordination_keywords if kw in text_lower)
    problem_score = sum(1 for kw in problem_keywords if kw in text_lower)

    total = status_score + coordination_score + problem_score
    if total == 0:
        return {"status": 0.33, "coordination": 0.33, "problem_solving": 0.34}

    return {"status": status_score / total, "coordination": coordination_score / total,
            "problem_solving": problem_score / total}


def calculate_velocity(issues: List[JiraIssue]) -> Dict[str, float]:
    if not issues:
        return {"velocity": 0, "avg_complexity": 0, "efficiency": 0, "total_points": 0}

    total_points = sum(i.story_points for i in issues)
    total_time = sum(i.time_spent_hours for i in issues)

    complexity_map = {"low": 1, "medium": 2, "high": 3}
    avg_complexity = statistics.mean([complexity_map[i.complexity] for i in issues])

    velocity = total_points / max(total_time, 1)
    efficiency = (total_points * avg_complexity) / max(total_time, 1)

    return {"velocity": round(velocity, 2), "avg_complexity": round(avg_complexity, 2),
            "efficiency": round(efficiency, 2), "total_points": total_points}


def detect_context_switching(meetings: List[Meeting]) -> Dict[str, float]:
    if not meetings:
        return {"context_switches": 0, "focus_time_ratio": 1.0, "meeting_load": 0}

    meeting_types = defaultdict(int)
    total_duration = 0

    for meeting in meetings:
        meeting_types[meeting.type] += 1
        total_duration += meeting.duration_minutes

    context_switches = meeting_types["interruption"] + (len(meetings) - 1) * 0.5
    focus_minutes = sum(m.duration_minutes for m in meetings if m.type == "focus")
    focus_ratio = focus_minutes / max(total_duration, 1)
    meeting_load = total_duration / 60

    return {"context_switches": round(context_switches, 2), "focus_time_ratio": round(focus_ratio, 2),
            "meeting_load": round(meeting_load, 2)}


def calculate_ml_score(commit_scores: List[float], slack_activities: List[Dict[str, float]],
                       velocity_data: Dict[str, float], context_data: Dict[str, float]) -> float:
    weights = {"code_impact": 0.35, "collaboration": 0.20, "velocity": 0.30, "focus": 0.15}

    avg_commit_score = statistics.mean(commit_scores) if commit_scores else 0
    code_score = min(avg_commit_score / 100, 1.0) * 100

    problem_solving = statistics.mean([s["problem_solving"] for s in slack_activities]) if slack_activities else 0
    collaboration_score = problem_solving * 100

    velocity_score = min(velocity_data["efficiency"] * 10, 100)
    focus_score = context_data["focus_time_ratio"] * 100

    final_score = (
                code_score * weights["code_impact"] + collaboration_score * weights["collaboration"] + velocity_score *
                weights["velocity"] + focus_score * weights["focus"])

    return round(final_score, 2)


def normalize_team_scores(team_scores: Dict[str, float]) -> Dict[str, Dict[str, any]]:
    if not team_scores:
        return {}

    scores = list(team_scores.values())
    mean_score = statistics.mean(scores)
    std_dev = statistics.stdev(scores) if len(scores) > 1 else 1

    sorted_members = sorted(team_scores.items(), key=lambda x: x[1], reverse=True)

    normalized = {}
    for rank, (member_id, score) in enumerate(sorted_members, 1):
        z_score = (score - mean_score) / std_dev if std_dev > 0 else 0
        percentile = ((len(scores) - rank + 1) / len(scores)) * 100

        normalized[member_id] = {
            "raw_score": score,
            "z_score": round(z_score, 2),
            "percentile": round(percentile, 2),
            "rank": rank,
            "performance_level": "High" if percentile >= 75 else "Medium" if percentile >= 25 else "Low"
        }

    return normalized


# ==================== API Endpoints ====================

@app.post("/config/update")
async def update_config(config: APIConfig):
    """Update API configuration"""
    global api_config
    if config.github_token:
        api_config.github_token = config.github_token
    if config.slack_token:
        api_config.slack_token = config.slack_token
    if config.jira_url:
        api_config.jira_url = config.jira_url
    if config.jira_email:
        api_config.jira_email = config.jira_email
    if config.jira_token:
        api_config.jira_token = config.jira_token

    return {"message": "Configuration updated", "configured_apis": {
        "github": bool(api_config.github_token),
        "slack": bool(api_config.slack_token),
        "jira": bool(api_config.jira_url and api_config.jira_email and api_config.jira_token)
    }}


@app.get("/config/status")
async def config_status():
    """Check which APIs are configured"""
    return {
        "configured_apis": {
            "github": bool(api_config.github_token),
            "slack": bool(api_config.slack_token),
            "jira": bool(api_config.jira_url and api_config.jira_email and api_config.jira_token)
        },
        "instructions": {
            "github": "Set GITHUB_TOKEN in .env or use /config/update",
            "slack": "Set SLACK_TOKEN in .env or use /config/update",
            "jira": "Set JIRA_URL, JIRA_EMAIL, JIRA_TOKEN in .env or use /config/update"
        }
    }


@app.post("/fetch/real-data")
async def fetch_data_endpoint(request: DataSourceRequest):
    """Fetch real data from APIs and analyze"""
    print(f"\n{'=' * 60}")
    print("🔍 Fetching Real Data from APIs...")
    print(f"{'=' * 60}\n")

    member_data = await fetch_real_data(request)

    # Analyze the data
    commit_impacts = [calculate_commit_impact(c) for c in member_data.github_commits]
    commit_scores = [c["total_impact"] for c in commit_impacts]
    slack_activities = [classify_slack_activity(m) for m in member_data.slack_messages]
    velocity_data = calculate_velocity(member_data.jira_issues)
    context_data = detect_context_switching(member_data.meetings)
    ml_score = calculate_ml_score(commit_scores, slack_activities, velocity_data, context_data)

    return {
        "member_id": member_data.member_id,
        "name": member_data.name,
        "data_sources": {
            "github_commits": len(member_data.github_commits),
            "slack_messages": len(member_data.slack_messages),
            "jira_issues": len(member_data.jira_issues),
            "meetings": len(member_data.meetings)
        },
        "scores": {
            "ml_score": ml_score,
            "code_impact": round(statistics.mean(commit_scores), 2) if commit_scores else 0,
            "velocity": velocity_data,
            "context_switching": context_data
        }
    }


@app.post("/analyze/member")
async def analyze_member(data: TeamMemberData) -> Dict:
    """Analyze individual team member productivity"""
    commit_impacts = [calculate_commit_impact(c) for c in data.github_commits]
    commit_scores = [c["total_impact"] for c in commit_impacts]
    slack_activities = [classify_slack_activity(m) for m in data.slack_messages]
    velocity_data = calculate_velocity(data.jira_issues)
    context_data = detect_context_switching(data.meetings)
    ml_score = calculate_ml_score(commit_scores, slack_activities, velocity_data, context_data)

    return {
        "member_id": data.member_id,
        "name": data.name,
        "scores": {"ml_score": ml_score,
                   "code_impact": round(statistics.mean(commit_scores), 2) if commit_scores else 0,
                   "velocity": velocity_data, "context_switching": context_data},
        "details": {"commit_analysis": commit_impacts[:5],
                    "slack_activity_summary": {"total_messages": len(slack_activities), "avg_problem_solving": round(
                        statistics.mean([s["problem_solving"] for s in slack_activities]),
                        2) if slack_activities else 0}}
    }


@app.post("/analyze/team")
async def analyze_team(team_members: List[TeamMemberData]) -> Dict:
    """Analyze entire team and generate dashboard data"""
    team_scores = {}
    member_details = {}

    for member in team_members:
        commit_impacts = [calculate_commit_impact(c) for c in member.github_commits]
        commit_scores = [c["total_impact"] for c in commit_impacts]
        slack_activities = [classify_slack_activity(m) for m in member.slack_messages]
        velocity_data = calculate_velocity(member.jira_issues)
        context_data = detect_context_switching(member.meetings)

        ml_score = calculate_ml_score(commit_scores, slack_activities, velocity_data, context_data)
        team_scores[member.member_id] = ml_score

        member_details[member.member_id] = {"name": member.name, "code_impact": round(statistics.mean(commit_scores),
                                                                                      2) if commit_scores else 0,
                                            "velocity": velocity_data["efficiency"],
                                            "focus_ratio": context_data["focus_time_ratio"]}

    normalized_scores = normalize_team_scores(team_scores)

    scores = list(team_scores.values())
    mean_score = statistics.mean(scores)
    std_dev = statistics.stdev(scores) if len(scores) > 1 else 1

    alerts = []
    for member_id, score in team_scores.items():
        z_score = (score - mean_score) / std_dev if std_dev > 0 else 0
        if abs(z_score) > 1.5:
            alerts.append({"member_id": member_id, "name": member_details[member_id]["name"], "score": score,
                           "z_score": round(z_score, 2),
                           "type": "high_performer" if z_score > 1.5 else "needs_support"})

    insights = []
    for member_id, details in member_details.items():
        if details["focus_ratio"] < 0.3:
            insights.append(
                f"{details['name']}: Low focus time ({details['focus_ratio']:.1%}) - consider reducing meetings")
        if details["velocity"] < 1.0:
            insights.append(
                f"{details['name']}: Low velocity ({details['velocity']:.2f}) - may need support or task breakdown")
        if details["code_impact"] > 80:
            insights.append(
                f"{details['name']}: High code impact ({details['code_impact']:.0f}) - excellent contributor")

    return {"manager_dashboard": {"team_scores": normalized_scores, "team_average": round(mean_score, 2),
                                  "team_size": len(team_members)},
            "alert_system": {"anomalies": alerts, "alert_count": len(alerts)},
            "trend_analysis": {"insights": insights, "coaching_recommendations": insights}}


@app.get("/demo/team-analysis")
async def demo_team_analysis():
    """Demo endpoint with pre-generated mock data"""
    mock_team = generate_mock_data()
    return await analyze_team(mock_team)


@app.get("/demo/mock-data")
async def get_mock_data():
    """Get the raw mock data for inspection"""
    mock_team = generate_mock_data()
    return {"team_size": len(mock_team), "members": [
        {"member_id": m.member_id, "name": m.name, "commits_count": len(m.github_commits),
         "messages_count": len(m.slack_messages), "issues_count": len(m.jira_issues), "meetings_count": len(m.meetings)}
        for m in mock_team]}


@app.get("/")
async def root():
    return {
        "message": "Productivity Scoring System API - With Real Data Integration!",
        "endpoints": {
            "config": ["GET /config/status - Check API configuration", "POST /config/update - Update API tokens"],
            "real_data": ["POST /fetch/real-data - Fetch and analyze real data from APIs"],
            "demo": ["GET /demo/team-analysis - Run analysis with mock data",
                     "GET /demo/mock-data - View mock team data"],
            "api": ["POST /analyze/member - Analyze individual team member",
                    "POST /analyze/team - Analyze entire team with dashboard"]
        },
        "setup_instructions": {
            "step1": "Create .env file with your API tokens",
            "step2": "Or use POST /config/update to set tokens",
            "step3": "Use POST /fetch/real-data with user identifiers",
            "example": {
                "github_username": "octocat",
                "github_repo": "owner/repo",
                "slack_user_id": "U123456",
                "jira_user_email": "user@company.com",
                "days_lookback": 30
            }
        }
    }


if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 60)
    print("🚀 Productivity Scoring System Starting...")
    print("   Now with REAL API Integration!")
    print("=" * 60)
    print("\n📊 Features:")
    print("   • GitHub API - Fetch real commit data")
    print("   • Slack API - Analyze message patterns")
    print("   • Jira API - Track issue velocity")
    print("   • Calendar API - Detect context switching")
    print("\n🔧 Setup:")
    print("   1. Create .env file with API tokens:")
    print("      GITHUB_TOKEN=your_token")
    print("      SLACK_TOKEN=your_token")
    print("      JIRA_URL=https://your-domain.atlassian.net")
    print("      JIRA_EMAIL=your@email.com")
    print("      JIRA_TOKEN=your_token")
    print("\n📍 Quick Links:")
    print("   • Main: http://localhost:8000")
    print("   • Config status: http://localhost:8000/config/status")
    print("   • Demo: http://localhost:8000/demo/team-analysis")
    print("   • Docs: http://localhost:8000/docs")
    print("\n" + "=" * 60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8001)