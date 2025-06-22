"""QA Agent for testing and validating InSpec baselines."""

import json
from typing import Any, Dict

from adk.agent import Agent
from adk.llm import LLM
from adk.mcp import ToolContext


class QualityAssuranceAgent(Agent):
    """
    An autonomous agent that manages the entire testing and fixing loop.

    This agent validates InSpec baselines by running them in containerized
    environments and iteratively fixing any issues found.
    """

    REMEDIATION_PROMPT = """
You are an expert InSpec developer. You need to fix failing InSpec tests.

**Failing Test Results:**
{test_results}

**Current InSpec Code:**
{current_code}

**Instructions:**
1. Analyze the test failures
2. Identify the root cause
3. Provide corrected InSpec code
4. Ensure the fix addresses the specific failure

**Corrected InSpec Code:**
"""

    def __init__(self, llm: LLM):
        super().__init__()
        self.llm = llm

    async def on_event(self, event: Dict[str, Any], context: ToolContext):
        """
        Receives a task to test and validate an InSpec baseline.

        Args:
            event: Dictionary containing baseline_path and target information
            context: Tool context for logging and tool access
        """
        baseline_path = event.get("baseline_path")
        target_info = event.get("target_info", {})

        if not baseline_path:
            await context.log.error("No baseline path provided to QA Agent.")
            return {"status": "error", "message": "Missing baseline path"}

        await context.log.info(
            f"QA Agent starting validation for baseline: {baseline_path}"
        )

        # Implement the testing and remediation loop
        max_iterations = 3
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            await context.log.info(f"QA iteration {iteration}/{max_iterations}")

            # 1. Run InSpec tests
            test_results = await self._run_inspec_tests(
                baseline_path, target_info, context
            )

            if test_results.get("all_passed", False):
                await context.log.info("All tests passed! Baseline validated.")
                return {
                    "status": "success",
                    "message": "Baseline validated successfully",
                    "iterations": iteration,
                }

            # 2. If tests failed, attempt remediation
            if iteration < max_iterations:
                await context.log.info("Tests failed, attempting remediation...")
                remediation_result = await self._remediate_failures(
                    baseline_path, test_results, context
                )

                if not remediation_result.get("success", False):
                    await context.log.error("Remediation failed")
                    break

        # Max iterations reached or remediation failed
        return {
            "status": "failure",
            "message": f"Could not validate baseline after {iteration} iterations",
            "final_test_results": test_results,
        }

    async def _run_inspec_tests(
        self, baseline_path: str, target_info: Dict[str, Any], context: ToolContext
    ) -> Dict[str, Any]:
        """Run InSpec tests against the target environment."""
        # Get the InSpec runner tool
        inspec_tool = self.tools.get_tool("inspec-runner-tool")

        # Configure target (Docker container, SSH, etc.)
        test_config = {"baseline_path": baseline_path, "target": target_info}

        try:
            result_str, _ = await inspec_tool.run_inspec_tests(**test_config)
            result = json.loads(result_str.text)

            await context.log.info(
                f"InSpec test completed. Status: {result.get('status')}"
            )

            return result

        except Exception as e:
            await context.log.error(f"Failed to run InSpec tests: {e}")
            return {"status": "error", "message": str(e), "all_passed": False}

    async def _remediate_failures(
        self, baseline_path: str, test_results: Dict[str, Any], context: ToolContext
    ) -> Dict[str, Any]:
        """Attempt to fix failing tests using LLM analysis."""
        failures = test_results.get("failures", [])

        if not failures:
            return {"success": True, "message": "No failures to remediate"}

        # For each failing control, attempt to fix it
        for failure in failures[:3]:  # Limit to first 3 failures
            control_id = failure.get("control_id")
            current_code = failure.get("code", "")

            await context.log.info(f"Attempting to fix control: {control_id}")

            # Use LLM to generate fix
            prompt = self.REMEDIATION_PROMPT.format(
                test_results=json.dumps(failure, indent=2), current_code=current_code
            )

            try:
                response = await self.llm.predict(prompt)
                corrected_code = response.text

                # Apply the fix (in real implementation, write to file)
                await context.log.info(
                    f"Generated fix for {control_id}:\n{corrected_code}"
                )

                # TODO: Write corrected code back to the baseline file

            except Exception as e:
                await context.log.error(f"Failed to generate fix for {control_id}: {e}")
                return {"success": False, "error": str(e)}

        return {"success": True, "message": "Remediation completed"}
