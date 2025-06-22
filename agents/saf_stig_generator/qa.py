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
            output_key="remediated_code",
        )

        super().__init__(name=name, llm_agent=llm_agent, sub_agents=[llm_agent])

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
                content={"error": "No baseline path provided to QA Agent."},
            )
            return

        # Implement the testing and remediation loop
        max_iterations = 3

        for iteration in range(max_iterations):
            # Test the baseline
            test_passed = await self._test_baseline(baseline_path, target_info, ctx)

            if test_passed:
                yield Event(
                    author=self.name,
                    content={"status": "success", "message": "All tests passed!"},
                )
                return

            # If tests failed and we have iterations left, try to fix
            if iteration < max_iterations - 1:
                await self._remediate_failures(baseline_path, ctx)
            else:
                yield Event(
                    author=self.name,
                    content={"status": "failed", "message": "Max iterations reached"},
                )

    async def _test_baseline(
        self, baseline_path: str, target_info: Dict[str, Any], ctx: InvocationContext
    ) -> bool:
        """Test the baseline and return True if all tests pass."""
        # This would integrate with your InSpec runner tool
        # For now, using placeholder logic based on session state
        test_results = ctx.session.state.get("test_results", {})
        return test_results.get("all_passed", False)

    async def _remediate_failures(self, baseline_path: str, ctx: InvocationContext):
        """Attempt to fix test failures using the LLM."""
        test_results = ctx.session.state.get("test_results", {})
        current_code = ctx.session.state.get("current_baseline_code", "")

        # Format the remediation prompt
        formatted_prompt = self.REMEDIATION_PROMPT.format(
            test_results=json.dumps(test_results.get("failures", []), indent=2),
            current_code=current_code,
        )

        # Update session state for the LLM
        ctx.session.state["remediation_prompt"] = formatted_prompt

        # Run the LLM agent to get remediated code
        async for event in self.llm_agent.run_async(ctx):
            # The remediated code will be in session state as "remediated_code"
            pass
