import os
import requests
import json
import google.generativeai as genai

# =========================
# CONFIG
# =========================
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API = "https://api.github.com"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-1.5-flash"  # fast + cheap
# alt: gemini-1.5-pro (higher reasoning)

# =========================
# INIT GEMINI
# =========================
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)

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
        "Return ONLY a valid JSON object with exactly four numeric fields:\n"
        "BasePoints, Difficulty, PeerKudos, BlockerPenalty.\n"
        "No explanations. No markdown. No extra text."
    )

    user_prompt = f"""
Analyze the following Git diff and return scores as JSON:

{diff_text}
"""

    response = model.generate_content(
        [
            {"role": "user", "parts": [system_prompt + "\n" + user_prompt]}
        ],
        generation_config={
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
        "BasePoints": max(0.0, float(scores.get("BasePoints", 0))),
        "Difficulty": max(0.0, float(scores.get("Difficulty", 1))),
        "PeerKudos": max(0.0, float(scores.get("PeerKudos", 0))),
        "BlockerPenalty": max(0.0, float(scores.get("BlockerPenalty", 0))),
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
        ai_scores["BasePoints"],
        ai_scores["Difficulty"],
        ai_scores["PeerKudos"],
        ai_scores["BlockerPenalty"],
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
