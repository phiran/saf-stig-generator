"""Coding Agent for implementing InSpec controls."""

import json
from typing import AsyncGenerator

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event


class CodingAgent(BaseAgent):
    """
    An LLM-powered agent that writes InSpec code.

    It is guided by retrieving examples of previously successful code
    from its long-term memory.
    """

    # Declare the LLM agent as a field for Pydantic
    llm_agent: LlmAgent

    # Allow arbitrary types for Pydantic
    model_config = {"arbitrary_types_allowed": True}

    # This prompt template includes a section for examples from memory.
    PROMPT_TEMPLATE = """
You are an expert InSpec developer for security hardening. Your task is to 
write the complete, executable InSpec code for a given STIG control.

Use the provided examples of high-quality, previously validated code to guide 
your work. The examples show the correct syntax and common patterns.

**Control to Implement (from STIG XML):**
{control_to_implement}

---

**Validated Examples from Memory (if any):**
{examples}

---

**Your Full InSpec Code Block:**
"""

    def __init__(self, name: str, model: str = "gemini-2.0-flash"):
        # Create the LLM agent for this coding agent
        llm_agent = LlmAgent(
            name=f"{name}_llm",
            model=model,
            instruction=self.PROMPT_TEMPLATE,
            output_key="implemented_code",
        )

        super().__init__(name=name, llm_agent=llm_agent, sub_agents=[llm_agent])

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Implements the coding logic using the new ADK pattern.
        """
        # Get the control stub from the session state
        control_stub = ctx.session.state.get("control_stub")
        if not control_stub or "description" not in control_stub:
            # Log error and return early
            yield Event(
                author=self.name,
                content={"error": "Invalid control stub provided to CodingAgent."},
            )
            return

        # 1. Query the memory tool to retrieve relevant code examples
        # Note: This would need to be adapted based on your memory tool implementation
        examples_text = "No relevant examples found in memory."

        # For now, we'll skip the memory lookup and proceed with code generation
        # TODO: Implement memory tool integration

        # 2. Set up the session state with the formatted prompt
        formatted_prompt = self.PROMPT_TEMPLATE.format(
            control_to_implement=json.dumps(control_stub, indent=2),
            examples=examples_text,
        )

        # Update the LLM agent's instruction with the formatted prompt
        ctx.session.state["coding_prompt"] = formatted_prompt
        ctx.session.state["control_stub"] = control_stub

        # 3. Run the LLM agent to generate the InSpec code
        async for event in self.llm_agent.run_async(ctx):
            yield event
        # 4. Handle the LLM response
        # In a real implementation, save to file and notify orchestrator
        if "implemented_code" in ctx.session.state:
            implemented_code = ctx.session.state["implemented_code"]
            yield Event(
                author=self.name,
                content={
                    "status": "success",
                    "message": "InSpec code implemented successfully.",
                    "code": implemented_code,
                },
            )
