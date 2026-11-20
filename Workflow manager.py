import asyncio
import json
import os
from datetime import datetime, timezone
from urllib import request, error


class AutonomousAgentOrchestrator:
    def __init__(self, agent_name: str, api_endpoint: str = "", api_key: str = ""):
        self.agent_name = agent_name
        self.api_endpoint = api_endpoint or os.getenv("AGENT_API_ENDPOINT", "")
        self.api_key = api_key or os.getenv("AGENT_API_KEY", "")
        self.memory_context = []

    def _call_external_api(self, payload: dict, timeout_sec: float = 10.0) -> dict:
        """Send a JSON payload to a real HTTP endpoint and parse the JSON response."""
        if not self.api_endpoint:
            raise ValueError("API endpoint is not configured.")

        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"{self.agent_name}/1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        body = json.dumps(payload).encode("utf-8")
        req = request.Request(self.api_endpoint, data=body, headers=headers, method="POST")

        with request.urlopen(req, timeout=timeout_sec) as resp:
            raw_data = resp.read().decode("utf-8")
            return json.loads(raw_data) if raw_data else {}

    def _process_step_data(self, step_id: int, objective: str, current_data: dict) -> dict:
        """Transform or enrich real data for each workflow stage."""
        processed = dict(current_data)
        processed["last_step"] = step_id
        processed["objective"] = objective
        processed["processed_at"] = datetime.now(timezone.utc).isoformat()

        if step_id == 1:
            # Step 1: Normalize incoming trigger data
            raw_input = processed.get("raw_input", "")
            processed["normalized_text"] = " ".join(str(raw_input).strip().split())
            processed["char_count"] = len(processed["normalized_text"])

        elif step_id == 2:
            # Step 2: Extract simple intent & keywords from real text
            text_lower = processed.get("normalized_text", "").lower()
            if any(word in text_lower for word in ["report", "summary", "analyze"]):
                intent = "analysis_and_reporting"
            elif any(word in text_lower for word in ["alert", "error", "fix"]):
                intent = "incident_response"
            else:
                intent = "general_workflow_execution"
            processed["detected_intent"] = intent

        elif step_id == 3:
            # Step 3: Build API request payload from processed context
            processed["api_payload"] = {
                "agent": self.agent_name,
                "intent": processed.get("detected_intent", "general_workflow_execution"),
                "input": processed.get("normalized_text", ""),
                "history_count": len(self.memory_context),
            }

        elif step_id == 4:
            # Step 4: Validate API response or fallback output
            api_result = processed.get("api_result", {})
            processed["validated"] = isinstance(api_result, dict) and len(api_result) > 0

        return processed

    async def execute_task_step(self, step_id: int, objective: str, context_data: dict) -> tuple[bool, dict]:
        print(f"[{self.agent_name}] Executing Step {step_id}: {objective}...")
        updated_data = self._process_step_data(step_id, objective, context_data)

        if step_id == 3:
            try:
                # Run blocking network I/O in a worker thread so the event loop stays non-blocking
                api_response = await asyncio.to_thread(
                    self._call_external_api,
                    updated_data["api_payload"],
                )
                updated_data["api_result"] = api_response
                updated_data["mode"] = "live_api"
                print(f"[{self.agent_name}] Live API response received in Step {step_id}.")
            except (error.URLError, error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
                print(f"[{self.agent_name}] API call failed in Step {step_id} ({exc}). Activating local fallback...")
                updated_data["api_result"] = {
                    "status": "fallback_processed",
                    "summary": f"Processed locally: {updated_data.get('normalized_text', '')}",
                }
                updated_data["mode"] = "local_fallback"
                print(f"[{self.agent_name}] Fallback completed for Step {step_id}.")

        self.memory_context.append({
            "step_id": step_id,
            "objective": objective,
            "mode": updated_data.get("mode", "local_processing"),
            "timestamp": updated_data["processed_at"],
        })
        return True, updated_data

    async def run_workflow(self, workflow_steps: list[str], initial_payload: dict) -> dict:
        print(f"--- Starting Agentic Workflow for: {self.agent_name} ---")
        state = dict(initial_payload)

        for idx, step in enumerate(workflow_steps, 1):
            ok, state = await self.execute_task_step(idx, step, state)
            if not ok:
                print(f"Workflow halted at step {idx}.")
                state["completed"] = False
                return state

        state["completed"] = True
        print("--- Workflow Completed Successfully ---")
        return state


if __name__ == "__main__":
    orchestrator = AutonomousAgentOrchestrator(
        agent_name="Gemini-Master-Agent",
        api_endpoint=os.getenv("AGENT_API_ENDPOINT", ""),  # e.g. "https://httpbin.org/post" or your API URL
        api_key=os.getenv("AGENT_API_KEY", ""),
    )

    steps = [
        "Ingest Enterprise Trigger",
        "Decompose Multi-Modal Intent",
        "Execute API Tool Synthesis",
        "Validate Telemetry Output",
    ]

    sample_input = {
        "source": "field_sensor_stream",
        "raw_input": "  Analyze soil moisture telemetry and generate a summary report for the green zone.  ",
    }

    final_state = asyncio.run(orchestrator.run_workflow(steps, sample_input))
    print("\nFinal Output State:")
    print(json.dumps(final_state, indent=2))

import asyncio
import json
import os
from datetime import datetime, timezone
from urllib import error, request


class AutonomousAgentOrchestrator:
    def __init__(
        self,
        agent_name: str,
        api_endpoint: str = "",
        api_key: str = "",
        allowed_scopes: list[str] | None = None,
    ):
        self.agent_name = agent_name
        self.api_endpoint = api_endpoint or os.getenv("AGENT_API_ENDPOINT", "")
        self.api_key = api_key or os.getenv("AGENT_API_KEY", "")
        self.allowed_scopes = allowed_scopes or ["jira:read", "jira:write", "confluence:read"]
        self.memory_context = []

    def _call_external_api(self, payload: dict, timeout_sec: float = 10.0) -> dict:
        """Send structured workflow payload to an external API/tool endpoint."""
        if not self.api_endpoint:
            raise ValueError("API endpoint is not configured.")

        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"{self.agent_name}/1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        body = json.dumps(payload).encode("utf-8")
        req = request.Request(self.api_endpoint, data=body, headers=headers, method="POST")

        with request.urlopen(req, timeout=timeout_sec) as resp:
            raw_data = resp.read().decode("utf-8")
            return json.loads(raw_data) if raw_data else {}

    def _ingest_workflow_trigger(self, data: dict) -> dict:
        """Step 1: Ingest trigger metadata, permission scopes, and raw request."""
        updated = dict(data)
        raw_input = updated.get("raw_input", "")
        requested_scopes = updated.get("scopes", ["jira:read", "confluence:read"])

        authorized_scopes = [s for s in requested_scopes if s in self.allowed_scopes]
        updated["trigger_source"] = updated.get("source", "atlassian_webhook")
        updated["normalized_input"] = " ".join(str(raw_input).strip().split())
        updated["authorized_scopes"] = authorized_scopes
        updated["permission_granted"] = len(authorized_scopes) > 0
        updated["ingested_at"] = datetime.now(timezone.utc).isoformat()
        return updated

    def _decompose_intent_and_tasks(self, data: dict) -> dict:
        """Step 2: Identify Atlassian workflow intent and break into actionable sub-tasks."""
        updated = dict(data)
        text_lower = updated.get("normalized_input", "").lower()

        if any(k in text_lower for k in ["jira", "ticket", "issue", "sprint", "update"]):
            workflow_domain = "jira_issue_automation"
            sub_tasks = [
                "fetch_jira_issue_context",
                "synthesize_status_update",
                "prepare_jira_payload",
            ]
        elif any(k in text_lower for k in ["confluence", "doc", "docs", "documentation", "page"]):
            workflow_domain = "confluence_knowledge_synthesis"
            sub_tasks = [
                "retrieve_confluence_pages",
                "extract_key_decisions",
                "format_documentation_summary",
            ]
        else:
            workflow_domain = "cross_product_workflow"
            sub_tasks = [
                "correlate_tickets_and_docs",
                "generate_action_plan",
                "dispatch_workflow_update",
            ]

        updated["workflow_domain"] = workflow_domain
        updated["sub_tasks"] = sub_tasks
        return updated

    def _build_execution_payload(self, data: dict) -> dict:
        """Step 3 helper: Build structured payload for API or tool execution."""
        return {
            "agent": self.agent_name,
            "source": data.get("trigger_source", "atlassian_webhook"),
            "workflow_domain": data.get("workflow_domain", "cross_product_workflow"),
            "authorized_scopes": data.get("authorized_scopes", []),
            "sub_tasks": data.get("sub_tasks", []),
            "input": data.get("normalized_input", ""),
            "memory_entries": len(self.memory_context),
        }

    def _validate_execution_result(self, data: dict) -> dict:
        """Step 4: Validate execution output, scope compliance, and telemetry."""
        updated = dict(data)
        result = updated.get("execution_result", {})
        has_result = isinstance(result, dict) and len(result) > 0
        has_scope = bool(updated.get("permission_granted"))

        updated["validated"] = bool(has_result and has_scope)
        updated["validation_status"] = "passed" if updated["validated"] else "failed_or_restricted"
        updated["validated_at"] = datetime.now(timezone.utc).isoformat()
        return updated

    async def execute_task_step(self, step_id: int, objective: str, state_data: dict) -> tuple[bool, dict]:
        print(f"[{self.agent_name}] Executing Step {step_id}: {objective}...")
        state = dict(state_data)
        state["current_step"] = step_id
        state["current_objective"] = objective
        mode = "local_processing"

        if step_id == 1:
            state = self._ingest_workflow_trigger(state)
            if not state["permission_granted"]:
                print(f"[{self.agent_name}] Permission denied for requested scopes.")
                return False, state

        elif step_id == 2:
            state = self._decompose_intent_and_tasks(state)

        elif step_id == 3:
            payload = self._build_execution_payload(state)
            state["execution_payload"] = payload
            try:
                api_response = await asyncio.to_thread(self._call_external_api, payload)
                state["execution_result"] = api_response
                mode = "live_api"
                print(f"[{self.agent_name}] Live API response received in Step {step_id}.")
            except (error.URLError, error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
                print(f"[{self.agent_name}] API unavailable ({exc}). Using local fallback in Step {step_id}...")
                state["execution_result"] = {
                    "status": "fallback_executed",
                    "workflow_domain": state.get("workflow_domain"),
                    "sub_tasks_planned": state.get("sub_tasks", []),
                    "summary": f"Prepared locally for: {state.get('normalized_input', '')}",
                }
                mode = "local_fallback"

        elif step_id == 4:
            state = self._validate_execution_result(state)

        state["last_mode"] = mode
        self.memory_context.append({
            "step_id": step_id,
            "objective": objective,
            "mode": mode,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return True, state

    async def run_workflow(self, workflow_steps: list[str], initial_payload: dict) -> dict:
        print(f"--- Starting Workflow for: {self.agent_name} ---")
        state = dict(initial_payload)

        for idx, step in enumerate(workflow_steps, 1):
            ok, state = await self.execute_task_step(idx, step, state)
            if not ok:
                state["completed"] = False
                print(f"Workflow halted at Step {idx}.")
                return state

        state["completed"] = True
        print("--- Workflow Completed Successfully ---")
        return state


if __name__ == "__main__":
    orchestrator = AutonomousAgentOrchestrator(
        agent_name="Atlassian-Workflow-Agent",
        api_endpoint=os.getenv("AGENT_API_ENDPOINT", ""),
        api_key=os.getenv("AGENT_API_KEY", ""),
    )

    steps = [
        "Ingest Workflow Trigger & Permissions",
        "Decompose Jira/Confluence Intent",
        "Execute API & Tool Synthesis",
        "Validate Execution Output",
    ]

    sample_trigger = {
        "source": "jira_and_confluence_sync",
        "scopes": ["jira:read", "jira:write", "confluence:read"],
        "raw_input": "  Summarize Confluence release notes and update related Jira tickets.  ",
    }

    final_output = asyncio.run(orchestrator.run_workflow(steps, sample_trigger))
    print("\nFinal Workflow Output:")
    print(json.dumps(final_output, indent=2))
