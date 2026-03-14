const BACKEND_URL = "http://127.0.0.1:8000";

const setStatus = (elementId, text) => {
  const el = document.getElementById(elementId);
  if (el) el.textContent = text;
};

const renderList = (selector, items, formatter) => {
  const container = document.getElementById(selector);
  if (!container) return;
  container.innerHTML = "";
  items.forEach((item) => {
    const li = document.createElement("li");
    li.innerHTML = formatter(item);
    container.appendChild(li);
  });
};

const refresh = async () => {
  try {
    const response = await fetch(`${BACKEND_URL}/dashboard/summary`);
    if (!response.ok) {
      throw new Error("Backend error");
    }
    const payload = await response.json();

    setStatus("agents-status", `${payload.total_agents} agents registered`);
    setStatus("active-count", `${payload.active_agent_count} active agents (last 5 min)`);
    renderList("active-list", payload.active_agents || [], (agent) => {
      const lastSeen = agent.last_heartbeat
        ? new Date(agent.last_heartbeat).toLocaleTimeString()
        : "unknown";
      return `
        <strong>${agent.name}</strong>
        <div class="muted">${agent.agent_id}</div>
        <div class="muted">Last heartbeat at ${lastSeen}</div>
      `;
    });

    setStatus("tasks-status", `${payload.recent_tasks.length || 0} tasks logged`);
    renderList("tasks-list", payload.recent_tasks || [], (task) => {
      return `
        <strong>${task.description}</strong>
        <div class="muted">By ${task.agent_id} · ${task.result_status}</div>
        <div class="muted">${task.execution_time}s</div>
      `;
    });

    setStatus("top-status", "Top reputations in the fleet");
    renderList("top-list", payload.top_agents || [], (agent) => {
      return `
        <strong>${agent.name}</strong>
        <div class="muted">Reputation ${agent.reputation_score.toFixed(2)}</div>
        <div class="muted">Caps: ${agent.capabilities.join(", ") || "—"}</div>
      `;
    });

    if (payload.recent_blocked_actions?.length > 0) {
      setStatus("blocked-status", `${payload.recent_blocked_actions.length} recent blocks`);
      renderList("blocked-list", payload.recent_blocked_actions, (log) => {
        return `
          <strong>${log.action_type}</strong>
          <div class="muted">${log.blocked_reason || log.reason}</div>
          <div class="muted">Agent: ${log.agent_id}</div>
        `;
      });
    } else {
      setStatus("blocked-status", "No blocked actions detected");
      document.getElementById("blocked-list").innerHTML = "";
    }
  } catch (error) {
    setStatus("agents-status", "Unable to reach backend");
  }
};

refresh();
setInterval(refresh, 15000);
