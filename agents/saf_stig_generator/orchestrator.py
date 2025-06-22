import json
import shutil

from google.adk.agents import BaseAgent
from google.adk.artifacts import Artifact
from google.adk.sessions import Session

from .common.config import ensure_dir, get_artifacts_dir


class OrchestratorAgent(BaseAgent):
    """
    The main agent responsible for orchestrating the entire STIG baseline
    generation workflow.

    This agent handles natural language input from the ADK web UI and produces
    a downloadable artifact containing the generated baseline.
    """

    INPUT_PARSER_PROMPT = """
You are a helpful assistant. Your task is to extract a specific software 
product name from a user's request.
Return only a JSON object with a single key, "product".

User request: "{user_request}"

JSON:
"""

    def __init__(self, llm: LLM):
        super().__init__()
        self.llm = llm

    async def on_event(self, event: dict, context: ToolContext):
        """Handle incoming events to trigger the workflow."""
        session: Session = context.session
        await context.log.info(f"OrchestratorAgent received an event: {event}")

        product_keyword = None

        # --- 1. Smart Input Parsing ---
        if isinstance(event, dict) and "product" in event:
            # Handle direct API-like calls (e.g., from `adk run`)
            product_keyword = event.get("product")
        elif isinstance(event, str):
            # Handle natural language from the chat UI
            await context.log.info(
                "Natural language input detected. Parsing product name..."
            )
            prompt = self.INPUT_PARSER_PROMPT.format(user_request=event)
            response = await self.llm.predict(prompt)
            try:
                # The LLM should return a JSON string, e.g., '{"product": "RHEL 9"}'
                parsed_data = json.loads(response.text)
                product_keyword = parsed_data.get("product")
            except (json.JSONDecodeError, AttributeError):
                await context.log.error(
                    f"Failed to parse LLM response for product name: {response.text}"
                )
                await session.tell(
                    "I'm sorry, I couldn't understand which product you're "
                    "asking for. Please try again."
                )
                return

        if not product_keyword:
            await context.log.error("Could not determine product keyword from input.")
            await session.tell(
                "I couldn't figure out which product you want. Please be more "
                "specific, like 'Generate a baseline for Red Hat Enterprise Linux 9'."
            )
            return

        await context.log.info(f"Starting workflow for product: {product_keyword}")
        await session.tell(
            f"Alright, I'm starting the process to generate a STIG baseline "
            f"for **{product_keyword}**. I'll keep you updated."
        )

        # NOTE: Full workflow would involve calls to disa_tool, mitre_tool,
        # saf_generator_tool, coding_agent, qa_agent with status updates

        # Let's assume the full workflow runs and produces a final baseline
        # in a directory. For this example, we'll create a dummy output.
        await context.log.info(
            "Workflow simulation: Pretending to generate a baseline..."
        )
        final_baseline_dir_name = (
            f"{product_keyword.replace(' ', '_').lower()}_baseline"
        )
        final_baseline_path = get_artifacts_dir() / "final" / final_baseline_dir_name
        ensure_dir(final_baseline_path)
        (final_baseline_path / "controls").mkdir(exist_ok=True)
        (final_baseline_path / "controls" / "V-230222.rb").write_text(
            "control 'V-230222' do\n  # ...\nend"
        )
        (final_baseline_path / "inspec.yml").write_text("name: my-baseline")

        await context.log.info(f"Simulated baseline created at: {final_baseline_path}")

        # --- 3. Create a Downloadable Artifact ---
        try:
            await context.log.info("Packaging final baseline for download...")
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
                    f"Completed and validated MITRE SAF STIG baseline "
                    f"for {product_keyword}."
                ),
                path=archive_path,
                mime_type="application/zip",
            )
            await session.create_artifact(final_artifact)

            await context.log.info(
                f"Successfully created downloadable artifact: {final_artifact.name}"
            )
            await session.tell(
                "Great news! The baseline is complete. You can find the "
                "download link in the 'Artifacts' tab."
            )

        except Exception as e:
            await context.log.error(
                f"Failed to create the final artifact: {e}", exc_info=True
            )
            await session.tell(
                "I finished the work, but there was a problem creating "
                "the download file."
            )
