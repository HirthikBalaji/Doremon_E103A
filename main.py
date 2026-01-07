from fastapi import FastAPI, Path, HTTPException
from google import genai
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="WorkScore Calculator API")

# You can add additional URLs to this list, for example, the frontend's production domain, or other frontends.
allowed_origins = [
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["X-Requested-With", "Content-Type"],
)



from pydantic import BaseModel, Field

from helper import *

# user_id = "ethan-arch"
from fastapi import FastAPI, Path, HTTPException
from typing import List
import json




@app.get("/users/{user_id}/data")
async def get_user_full_data(user_id: str = Path(..., description="The ID/username to fetch data for")):
    """
    Returns all raw activity data for a specific user across all platforms.
    """
    try:
        # 1. Load the raw data sources
        slack_data = load_json("slack_data.json")
        github_data = load_json("github_commits.json")
        transcripts_data = load_json("meeting.json")

        # 2. Extract user-specific records using your helper functions
        user_slack = get_user_slack_messages(slack_data, user_id)
        user_github = get_user_github_commits(github_data, user_id)
        user_meetings = get_user_meeting_transcripts_with_context(transcripts_data, user_id)

        # 3. Check if the user actually has any data
        if not user_slack and not user_github and not user_meetings:
            raise HTTPException(status_code=404, detail=f"No data found for user: {user_id}")

        # 4. Return the aggregated "Profile"
        return {
            "user_id": user_id,
            "stats": {
                "slack_message_count": len(user_slack),
                "github_commit_count": len(user_github),
                "meetings_attended": len(user_meetings)
            },
            "raw_data": {
                "slack": user_slack,
                "github": user_github,
                "meetings": user_meetings
            }
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Data file missing: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_all_registered_users() -> List[str]:
    """Extracts the predefined user list from the workspace JSON."""
    try:
        with open("slack_data.json", "r", encoding='utf-8') as f:
            data = json.load(f)
            # Accessing the "users" key directly from your JSON structure
            return data.get("users", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def discover_active_users() -> List[str]:
    """Scans channels to find users who actually sent messages."""
    active_users = set()
    try:
        with open("slack_data.json", "r",encoding='utf-8') as f:
            data = json.load(f)
            for channel in data.get("channels", []):
                for msg in channel.get("messages", []):
                    if "user" in msg:
                        active_users.add(msg["user"])
        return list(active_users)
    except Exception:
        return []


@app.get("/users", response_model=List[str])
async def list_users(discovery: bool = False):
    """
    Returns the list of users.
    Use ?discovery=true to scan message history for active users.
    """
    if discovery:
        users = discover_active_users()
    else:
        users = get_all_registered_users()

    if not users:
        raise HTTPException(status_code=404, detail="No users found in data source.")

    return sorted(users)


# Your existing POST /calculate-score/{user_id} goes here...
# Exact schema from your JSON
class AnalysisSummary(BaseModel):
    difficulty_rationale: str = Field(description="Rationale for difficulty level")
    kudos_evidence: List[str] = Field(description="List of quotes supporting kudos")
    penalty_evidence: List[str] = Field(description="List of incidents for penalties")

class Variables(BaseModel):
    base_points: int = Field(100, description="Base score")
    difficulty_factor: float = Field(0.0, description="Difficulty adjustment")
    peer_kudos_count: int = Field(0, description="Number of peer kudos")
    blocker_penalty_total: int = Field(0, description="Total penalty from blockers")

class ResponseSchema(BaseModel):
    analysis_summary: AnalysisSummary
    variables: Variables
@app.post("/calculate-score/{user_id}", response_model=ResponseSchema)
async def get_work_score(user_id: str = Path(..., description="The GitHub/Slack username")):
    try:
        slack_data = load_json("slack_data.json")
        github_data = load_json("github_commits.json")
        transcripts_data = load_json("meeting.json")

        slack_messages = get_user_slack_messages(slack_data, user_id)
        github_commits = get_user_github_commits(github_data, user_id)
        received_code = get_user_received_code(slack_data, user_id)
        meeting_flows = get_user_meeting_transcripts_with_context(
            transcripts_data,
            user_id,
            context_window=2
        )

        peer_kudos = extract_peer_kudos(slack_data, github_data, user_id)


        # Client reads GEMINI_API_KEY env var
        client = genai.Client()
        SOURCE = ''
        SOURCE += "\n🔹 Slack Messages"
        for m in slack_messages:
            SOURCE += str(m)

        SOURCE += "\n🔹 GitHub Commits"
        for c in github_commits:
            SOURCE += f"{c['sha'], '-', c['message']}"

        SOURCE += "\n🔹 Code Received from Teammates"
        for r in received_code:
            SOURCE += str(r)

        SOURCE += "\n🔹 Meeting Transcript Flow"
        for meeting in meeting_flows:
            SOURCE += f"\nMeeting {meeting['meeting_id']}"
            for line in meeting["flow"]:
                SOURCE += f"{line['user']}: {line['text']}"

        SOURCE += "\n🔹 Peer Kudos"
        for k in peer_kudos:
            if k["type"] == "slack_ack":
                SOURCE += f"{k['from_user']} shared code -> acknowledged by {k['to_user']} in Slack: {k['ack_text']}"
            else:
                SOURCE += f"{k['from_user']} shared code -> used by {k['to_user']} in GitHub commit {k['commit_sha']}"


        prompt = f"""**Instruction:** You are a data processing engine. Analyze the provided GitHub Diffs, Slack Messages, and Meeting Transcripts to calculate a `WorkScore`.
        Your goal is absolute, mathematical accuracy.
        Rules of Engagement:
        1. Zero-Shot Error Tolerance: You have zero tolerance for hallucination or approximation. If data is ambiguous, state the ambiguity rather than guessing.
        2. Recursive Verification: Before outputting a final response, you must draft three internal solutions. Compare them, check for logical fallacies, and only output the version that survives rigorous cross-examination.
        3. SOTA Standard: Operate at a level that exceeds the capabilities of standard models (GPT-4/Gemini Ultra). Your reasoning must be granular, step-by-step, and irrefutable.
        4. Citation & Logic: Every assertion must be backed by verifiable logic or data.
        **Input Data:**
        
        {SOURCE}
        
        Calculation Logic:
        
        1. BasePoints: Default to 10 unless specified otherwise.
        2. Difficulty 1 to 5: Based on Github Commits and codediff changes        
        3. PeerKudos (Count): Total count of unique instances of peer appreciation or public "thank-yous."
        4. BlockerPenalty (Flat Sum): Deduct 10 points for every instance where the user explicitly blocked progress, missed a deadline, or broke a build.
        
        **Constraint:** Return **ONLY** a valid JSON object. Do not include introductory text or markdown explanations.
    
        """
        print(prompt)
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": ResponseSchema.model_json_schema(),
            }
        )

        # Parse and save to file
        data = ResponseSchema.model_validate_json(response.text)
        with open('score_response.json', 'w') as f:
            json.dump(data.model_dump(), f, indent=2)

        print("Saved to score_response.json")
        print(json.dumps(data.model_dump(), indent=2))
        result = ResponseSchema.model_validate_json(response.text)
        # result.user_id = user_id  # Ensure the ID matches the request
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)