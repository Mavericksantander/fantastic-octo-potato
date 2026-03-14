import subprocess
from typing import Any

from sdk.avos_agent import AVOSAgent


RISKY_PATTERNS = [
    "rm -rf",
    "sudo",
    "chmod",
    "chown",
    "dd",
    "mkfs",
    "systemctl",
    "reboot",
    "shutdown",
    "/etc",
    "/usr/bin",
]


def _detect_risky_command(command: str) -> list[str]:
    lowered = command.lower()
    matches: list[str] = []
    for pattern in RISKY_PATTERNS:
        if pattern in lowered:
            matches.append(pattern)
    return matches


def _safe_run(command: str) -> dict[str, Any]:
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


class ActionFirewall:
    def __init__(self, agent: AVOSAgent):
        self.agent = agent

    def execute_shell_command(self, command: str) -> dict[str, Any]:
        """Check for risky commands, call the governance API, and block denied actions."""
        risk_factors = _detect_risky_command(command)
        payload: dict[str, Any] = {"command": command}
        if risk_factors:
            payload["risk_factors"] = risk_factors
            payload["requires_root"] = "sudo" in command.lower()
        decision = self.agent.authorize_action("execute_shell_command", payload)
        if decision.get("decision") != "allow":
            return {
                "status": "blocked",
                "decision": decision.get("decision"),
                "reason": decision.get("reason"),
                "risk_factors": risk_factors,
            }
        return {"status": "executed", **_safe_run(command)}
