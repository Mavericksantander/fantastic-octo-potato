<<<<<<< HEAD
# fantastic-octo-potato
=======
# ApexVeritasOS (AVOS) MVP

A governance platform for autonomous AI agents that provides identity, logging, and safety controls while being easy to spin up locally.

## Stack
- FastAPI backend with SQLite (craft to swap with PostgreSQL via `DATABASE_URL`).
- Python Agent SDK for interacting with the platform.
- Firewall middleware to intercept shell actions.
- Simple HTML/JS dashboard querying FastAPI.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
The server launches on `http://127.0.0.1:8000` and creates `avos.db` (SQLite).

## Registering a test agent
1. Use the SDK to register an agent and side-step manual HTTP cranking:
    ```python
    from sdk.avos_agent import AVOSAgent

    agent = AVOSAgent("research_bot", capabilities=["web_research", "data_ingest"])
    agent.register_agent()
    print(agent.public_key)
    ```
2. `register_agent` returns `agent_id` and `public_key`. Store the `public_key`; it acts as the API key for future calls.

## Logging a task & reputation
```python
agent.log_task("web research", result_status="success", execution_time=3.2)
```
Every successful task bumps the reputation score by `0.5`, failures subtract `1.0`, and the updated score is returned.

## Authorization testing
Ask the platform whether an agent may perform a risky action:
```python
decision = agent.authorize_action("execute_shell_command", {"command": "rm -rf /tmp/test"})
print(decision)
```
The API enforces rules such as blocking destructive shell commands, denying edits under `/etc`, requiring verification for large spending, and logging every authorization attempt.

## Action firewall demo
Incorporate the firewall module to block dangerous shell requests before they reach your agent framework:
```python
from firewall.action_firewall import ActionFirewall
firewall = ActionFirewall(agent)
firewall.execute_shell_command("rm -rf /tmp/sensitive")
```
If the backend denies the action, the firewall returns `status: blocked` and the command is not executed.

## Dashboard
Open `dashboard/index.html` in a browser (or serve it via any static server). It visualizes:
- Registered agents with reputation
- Recent tasks
- Reputation snapshots
- Blocked actions logged by the authorization API

It fetches data from `GET /dashboard/summary`, which aggregates agents, tasks, and denied authorizations.

## Environment overrides
- `DATABASE_URL` to point to PostgreSQL (e.g., `postgresql://user:pass@localhost/avos`).
- `AVOS_RATE_LIMIT`/`AVOS_RATE_WINDOW` for rate-limiting.

## Additional APIs
- **Heartbeat:** `POST /agents/{agent_id}/heartbeat` lets agents report their status and metadata.
- **Public directory:** `GET /agents/public` lists agents with reputation and capabilities for discovery.
- **Search:** `GET /agents/search?capability=<cap>&min_reputation=<score>` filters agents by capability and score.
- **Metrics:** `GET /metrics/blocked_actions` returns how many actions have been denied to date.

## OpenClaw integration & exposure
1. Run the API on all interfaces and expose it externally:
   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ngrok http 8000  # optional: share the generated https://*.ngrok.io URL with OpenClaw
   ```
2. OpenClaw bots call `/external/register_agent` to onboard. Include `developer_id`, `bot_name`, `capabilities`, and the shared `invite_code` (e.g. `AVOS-OPEN-2026`).
3. Store the returned `agent_id`/`public_key` and send it as `X-API-Key` for every follow-up request.

### OpenClaw sample payloads
```jsonc
// 1. Register the agent
POST /external/register_agent
Content-Type: application/json

{
  "developer_id": "openclaw_team",
  "bot_name": "openclaw_scout",
  "capabilities": ["web_scraping", "decisioning"],
  "invite_code": "AVOS-OPEN-2026"
}

// 2. Log a completed task after registration
POST /agent/{agent_id}/log_task
X-API-Key: <public_key>
Content-Type: application/json

{
  "agent_id": "<agent_id>",
  "task_description": "Harvest market data",
  "result_status": "success",
  "execution_time": 2.8
}

// 3. Request authorization before a risky command
POST /authorize_action
X-API-Key: <public_key>
Content-Type: application/json

{
  "agent_id": "<agent_id>",
  "action_type": "execute_shell_command",
  "action_payload": {"command": "rm -rf /tmp/reports"}
}
```
OpenClaw skill/webhook should send these requests sequentially, honoring `X-API-Key`.

## Simulation helper
Run `scripts/simulate_agents.py` to register a few agents, push heartbeat updates, log tasks, and trigger blocked shell commands so you can see the dashboard and logs populate quickly.

## Next steps
- Wire the firewall into OpenClaw or other agent runners (use `ActionFirewall` in your execution pipeline).
- Swap SQLite for PostgreSQL in production by setting `DATABASE_URL` and running migrations.
- Extend the dashboard with authentication and richer analytics.
>>>>>>> 64bae98 (feat: AVOS MVP)
