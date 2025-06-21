# agents/src/saf_gen/agents/coding_agent.py
import json

from adk.agent import Agent
from adk.llm import LLM
from adk.mcp import ToolContext


class CodingAgent(Agent):
    """
    An LLM-powered agent that writes InSpec code. It is guided by
    retrieving examples of previously successful code from its long-term memory.
    """

    # This new prompt template explicitly includes a section for examples.
    PROMPT_TEMPLATE = """
You are an expert InSpec developer for security hardening. Your task is to write the complete, executable InSpec code for a given STIG control.

Use the provided examples of high-quality, previously validated code to guide your work. The examples show the correct syntax and common patterns.

**Control to Implement (from STIG XML):**
{control_to_implement}

---

**Validated Examples from Memory (if any):**
{examples}

---

**Your Full InSpec Code Block:**
"""

    def __init__(self, llm: LLM):
        super().__init__()
        self.llm = llm

    async def on_event(self, event: dict, context: ToolContext):
        """
        Receives a task to implement a single InSpec control.
        """
        control_stub = event.get("control_stub")
        if not control_stub or "description" not in control_stub:
            await context.log.error("Invalid control stub provided to CodingAgent.")
            return

        await context.log.info(
            f"CodingAgent received task for: {control_stub.get('id')}"
        )

        # 1. Query the memory tool to retrieve relevant code examples
        memory_tool = self.tools.get_tool("memory-tool")

        query_result_str, _ = await memory_tool.query_memory(
            control_description=control_stub.get("description")
        )
        query_result = json.loads(query_result_str.text)

        examples_text = "No relevant examples found in memory."
        if query_result.get("status") == "success" and query_result.get("results"):
            # Format the retrieved code examples for the prompt
            example_codes = [result["code"] for result in query_result["results"]]
            examples_text = "\n\n---\n\n".join(example_codes)
            await context.log.info(
                f"Found {len(example_codes)} examples to guide code generation."
            )

        # 2. Construct the prompt for the LLM
        prompt = self.PROMPT_TEMPLATE.format(
            control_to_implement=json.dumps(control_stub, indent=2),
            examples=examples_text,
        )

        # 3. Call the LLM to generate the InSpec code
        await context.log.info("Generating InSpec code with guidance from memory...")
        generated_code_response = await self.llm.predict(prompt)
        generated_code = generated_code_response.text

        # 4. Return the result
        # In a real implementation, you'd save this to a file and notify the orchestrator
        await context.log.info(f"Generated code:\n{generated_code}")

        return {"status": "success", "implemented_code": generated_code}
