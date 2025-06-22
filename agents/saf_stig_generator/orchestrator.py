import shutil
from typing import AsyncGenerator

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.artifacts import Artifact
from google.adk.events import Event
from google.adk.sessions import Session

from .common.config import ensure_dir, get_artifacts_dir


class OrchestratorAgent(BaseAgent):
    """
    The main agent responsible for orchestrating the entire STIG baseline
    generation workflow.

    This agent handles natural language input from the ADK web UI and produces
    a downloadable artifact containing the generated baseline.
    """

    # Declare the LLM agent as a field for Pydantic
    llm_agent: LlmAgent

    # Allow arbitrary types for Pydantic
    model_config = {"arbitrary_types_allowed": True}

    INPUT_PARSER_PROMPT = """
# ROLE & GOAL
You are a highly accurate, automated request parsing engine. Your sole function is to extract key information (a software product and its version) from a user's request and format it as a single, clean JSON object. You do not hold conversations. You only output JSON.

# TASK
From the user's request, you must extract the following entities:
1.  `product`: The full name of the operating system or application (e.g., "Red Hat Enterprise Linux", "Windows Server").
2.  `version`: The specific version identifier (e.g., "9", "2022", "22.04").

# RULES
- Your output MUST be a single, valid JSON object and nothing else.
- DO NOT add any commentary, explanations, or markdown formatting like ```json.
- If a specific version is not mentioned in the request, the value for the "version" key MUST be `null`.
- Be as specific as possible when extracting the product name.

---
# EXAMPLES

## Example 1
User request: "I need the STIG for Red Hat Enterprise Linux 9."
JSON:
{
  "product": "Red Hat Enterprise Linux",
  "version": "9"
}

## Example 2
User request: "can you get me the baseline for rhel9?"
JSON:
{
  "product": "Red Hat Enterprise Linux",
  "version": "9"
}

## Example 3
User request: "Please generate one for Windows Server 2022."
JSON:
{
  "product": "Windows Server",
  "version": "2022"
}

## Example 4
User request: "Just the CIS baseline for Oracle Linux, please."
JSON:
{
  "product": "Oracle Linux",
  "version": null
}
---

# USER REQUEST TO PROCESS
User request: "{user_request}"

# JSON:
"""

    def __init__(self, name: str, model: str = "gemini-2.0-flash"):
        # Create the LLM agent for parsing input
        llm_agent = LlmAgent(
            name=f"{name}_llm",
            model=model,
            instruction=self.INPUT_PARSER_PROMPT,
            output_key="parsed_product",
        )

        super().__init__(name=name, llm_agent=llm_agent, sub_agents=[llm_agent])

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """Handle incoming workflow requests."""
        session: Session = ctx.session

        # Get product from session state (set by the ADK runtime)
        product_keyword = ctx.session.state.get("product")

        if not product_keyword:
            yield Event(
                author=self.name,
                content={"error": "No product specified in session state"},
            )
            return

        yield Event(
            author=self.name,
            content={
                "status": "started",
                "message": f"Starting STIG baseline generation for {product_keyword}",
            },
        )

        # --- Simulate the workflow ---
        # In a real implementation, this would orchestrate calls to:
        # - DISA STIG tool to get STIG data
        # - MITRE baseline tool to get baseline template
        # - Coding agent to implement controls
        # - QA agent to test and validate

        yield Event(
            author=self.name,
            content={
                "status": "progress",
                "message": "Generating baseline structure...",
            },
        )

        # Create the baseline structure
        final_baseline_dir_name = (
            f"{product_keyword.replace(' ', '_').lower()}_baseline"
        )
        final_baseline_path = get_artifacts_dir() / "final" / final_baseline_dir_name
        ensure_dir(final_baseline_path)
        (final_baseline_path / "controls").mkdir(exist_ok=True)
        (final_baseline_path / "controls" / "V-230222.rb").write_text(
            "control 'V-230222' do\n  # Sample control implementation\nend"
        )
        (final_baseline_path / "inspec.yml").write_text("name: my-baseline")

        # --- Create a Downloadable Artifact ---
        try:
            yield Event(
                author=self.name,
                content={
                    "status": "progress",
                    "message": "Packaging baseline for download...",
                },
            )

            # Create a zip file of the final directory
            archive_path_base = (
                get_artifacts_dir() / "archives" / final_baseline_dir_name
            )
            ensure_dir(archive_path_base.parent)

            archive_path = shutil.make_archive(
                base_name=str(archive_path_base),
                format="zip",
                root_dir=final_baseline_path.parent,
                base_dir=final_baseline_path.name,
            )

            # Register the zip file as a session artifact
            final_artifact = Artifact(
                name=f"{final_baseline_dir_name}.zip",
                description=(
                    f"Completed MITRE SAF STIG baseline for {product_keyword}."
                ),
                path=archive_path,
                mime_type="application/zip",
            )
            await session.create_artifact(final_artifact)

            yield Event(
                author=self.name,
                content={
                    "status": "success",
                    "message": "Baseline generation complete!",
                    "artifact_name": final_artifact.name,
                },
            )

        except Exception as e:
            yield Event(
                author=self.name,
                content={
                    "status": "error",
                    "message": f"Failed to create artifact: {str(e)}",
                },
            )
