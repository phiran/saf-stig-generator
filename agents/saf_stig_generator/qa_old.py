"""QA Agent for testing and validating InSpec baselines."""

import json
from typing import Any, AsyncGenerator, Dict

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event


class QualityAssuranceAgent(BaseAgent):
    """
    An autonomous agent that manages the entire testing and fixing loop.

    This agent validates InSpec baselines by running them in containerized
    environments and iteratively fixing any issues found.
    """

    # Declare the LLM agent as a field for Pydantic
    llm_agent: LlmAgent
    
    # Allow arbitrary types for Pydantic
    model_config = {"arbitrary_types_allowed": True}

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

    def __init__(self, name: str, model: str = "gemini-2.0-flash"):
        # Create the LLM agent for remediation
        llm_agent = LlmAgent(
            name=f"{name}_llm",
            model=model,
            instruction=self.REMEDIATION_PROMPT,
            output_key="remediated_code"
        )
        
        super().__init__(
            name=name,
            llm_agent=llm_agent,
            sub_agents=[llm_agent]
        )

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Implements the QA workflow using the new ADK pattern.
        """
        # Get baseline info from session state
        baseline_path = ctx.session.state.get("baseline_path")
        target_info = ctx.session.state.get("target_info", {})

        if not baseline_path:
            yield Event(
                author=self.name,
                content={"error": "No baseline path provided to QA Agent."}
            )
            return

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
