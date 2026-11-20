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

