import os
import requests
import json
import google.genai as genai
from dotenv import load_dotenv

load_dotenv('.env')
# =========================
# CONFIG
# =========================
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API = "https://api.github.com"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"  # fast + cheap
# alt: gemini-1.5-pro (higher reasoning)

# =========================
# INIT GEMINI
# =========================
client = genai.Client(api_key=GEMINI_API_KEY)


# =========================
# GITHUB DIFF FETCH
# =========================
def get_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.diff",
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text

# =========================
# GEMINI ANALYSIS
# =========================
def analyze_diff_with_ai(diff_text: str) -> dict:
    system_prompt = (
        "You are a senior engineering manager.\n"
        "Return ONLY a valid JSON object with only one variable.\n"
        "Difficulty.\n"
        "No explanations. No markdown. No extra text."
    )

    user_prompt = f"""
Analyze the following Git diff and return scores as JSON:

{diff_text}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            {
                "role": "user",
                "parts": [
                    {
                        "text": system_prompt + "\n" + user_prompt
                    }
                ]
            }
        ],
        config={
            "temperature": 0.2,
            "response_mime_type": "application/json"
        }
    )

    raw_text = response.text.strip()

    try:
        scores = json.loads(raw_text)
    except json.JSONDecodeError:
        print("❌ Gemini returned invalid JSON:")
        print(raw_text)
        return {
            "BasePoints": 0,
            "Difficulty": 1,
            "PeerKudos": 0,
            "BlockerPenalty": 0,
        }

    return {
        "Difficulty": max(0.0, float(scores.get("Difficulty", 1)))
    }

# =========================
# SCORING LOGIC
# =========================
def compute_final_score(base_points, difficulty, peer_kudos, blocker_penalty):
    return (base_points * difficulty) + (peer_kudos * 1.5) - blocker_penalty

def score_pull_request(owner: str, repo: str, pr_number: int) -> dict:
    diff_text = get_pr_diff(owner, repo, pr_number)
    ai_scores = analyze_diff_with_ai(diff_text)

    final_score = compute_final_score(
        10,
        ai_scores["Difficulty"],
        0,
        0,
    )

    ai_scores["FinalScore"] = round(final_score, 2)
    return ai_scores

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    OWNER = "HirthikBalaji"
    REPO = "Resume-Builder"
    PR_NUMBER = 1

    try:
        results = score_pull_request(OWNER, REPO, PR_NUMBER)
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"Error: {e}")

import requests
from datetime import datetime

# --- CONFIGURATION ---

USERNAME = 'HirthikBalaji'
REPO_FILTER = None  # Set to 'owner/repo' to track a specific repo, or None for all

HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

# --- POINT VALUES ---
POINTS_CONFIG = {
    "PUSH": 5,  # per commit
    "PR_OPEN": 20,  # per PR
    "PR_MERGE": 30,  # per merged PR
    "ISSUE": 10,  # per issue
    "REVIEW": 8,  # per PR approval/review
    "COMMENT": 2,  # per substantive comment
}


def get_github_activity(username):
    url = f"https://api.github.com/users/{username}/events"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return []
    return response.json()


def calculate_points(events):
    total_points = 0
    daily_commits = {}  # For the 50-commit cap

    for event in events:
        etype = event['type']
        created_at = event['created_at'][:10]  # YYYY-MM-DD

        # 1. Commits Pushed (PushEvent)
        if etype == 'PushEvent':
            commits_count = len(event['payload'].get('commits', []))
            daily_commits[created_at] = daily_commits.get(created_at, 0) + commits_count
            # Apply cap of 50 per day
            effective_commits = min(daily_commits[created_at], 50) - (daily_commits[created_at] - commits_count)
            if effective_commits > 0:
                total_points += effective_commits * POINTS_CONFIG["PUSH"]

        # 2. Pull Requests (PullRequestEvent)
        elif etype == 'PullRequestEvent':
            action = event['payload']['action']
            if action == 'opened':
                total_points += POINTS_CONFIG["PR_OPEN"]
            elif action == 'closed' and event['payload']['pull_request'].get('merged'):
                total_points += POINTS_CONFIG["PR_MERGE"]

        # 3. Issues Created (IssuesEvent)
        elif etype == 'IssuesEvent' and event['payload']['action'] == 'opened':
            total_points += POINTS_CONFIG["ISSUE"]

        # 4. Reviews Submitted (PullRequestReviewEvent)
        elif etype == 'PullRequestReviewEvent':
            total_points += POINTS_CONFIG["REVIEW"]

        # 5. Comments (IssueCommentEvent)
        elif etype == 'IssueCommentEvent' and event['payload']['action'] == 'created':
            comment_body = event['payload']['comment'].get('body', '')
            # Simple "substantive" check: more than 10 characters and not just an emoji
            if len(comment_body) > 10:
                total_points += POINTS_CONFIG["COMMENT"]

    return total_points


# Run it
activity_data = get_github_activity(USERNAME)
score = calculate_points(activity_data)
print(f"Total Activity Score for {USERNAME}: {score} points")