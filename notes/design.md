# **Solution Outline: ADK-Powered MITRE SAF STIG Baseline Generation**

This document outlines the architecture and development plan for an autonomous system, built using the Google Agent Development Kit (ADK), to generate and validate MITRE SAF InSpec baselines for user-specified products.

## **I. High-Level Architecture & Workflow**

The solution will be centered around an **Orchestrator Agent** that manages the end-to-end workflow by invoking specialized agents and a suite of modular, network-accessible tools (MCP Services).

**Core Workflow:**

1. **Initiation:** A user specifies the target product and version (e.g., "Red Hat Enterprise Linux 9").  
2. **STIG Acquisition:** The **Orchestrator Agent** calls the disa\_stig\_tool to download the official DISA STIG .zip package for the product.  
3. **Baseline Discovery:** The Orchestrator calls the mitre\_baseline\_tool to search GitHub for a pre-existing MITRE SAF baseline for the specified product.  
4. **Decision Point:**  
   * If a baseline exists: The Orchestrator proceeds directly to the QA phase (Step 7).  
   * If no baseline exists: The Orchestrator proceeds to generate a new one (Step 5).  
5. **Stub Generation:** The Orchestrator calls the saf\_generator\_tool, providing the downloaded DISA XCCDF file to create a skeleton InSpec baseline.  
6. **Code Implementation:** The Orchestrator invokes the **Coding Agent**, tasking it with implementing the Ruby/InSpec control logic for each vulnerability stub in the new baseline. The agent uses the memory\_tool to retrieve validated examples from the knowledge store to guide its code generation.  
7. **Quality Assurance:** The Orchestrator hands off the completed or pre-existing baseline to the **QA & Remediation Agent** for testing. The agent uses the docker\_tool and inspec\_runner\_tool to test and fix the baseline in a sandboxed environment.  
8. Validation Loop (QA Agent):  
   a. Calls the docker\_tool to find and pull a suitable Docker image for the target product.  
   b. Calls the inspec\_runner\_tool to execute the baseline against the running container.  
   c. Analyzes the test results. If failures occur, it iteratively corrects the InSpec code and re-runs the tests until all controls pass or are justifiably waived.  
9. **Learning & Memorization:** Upon successful validation by the QA Agent, the **Orchestrator Agent** calls the memory\_tool to add the newly perfected baseline to the knowledge store, improving the system for all future tasks.  
10. **Completion:** The final, validated InSpec baseline is packaged and presented as the final artifact.

## **II. Core Components: The Agents**

These are the "brains" of the operation, built using the Google ADK. They are designed with clear separation of concerns.

* **Orchestrator Agent (orchestrator\_agent.py)**  
  * **Responsibility:** Manages the overall workflow, makes logical decisions, and calls other agents and tools in the correct sequence. It maintains the state of the entire generation process.  
  * **Inputs:** Initial user request (product name, version).  
  * **Outputs:** The final, validated STIG baseline artifact.  
* **Coding Agent (coding\_agent.py)**  
  * **Responsibility:** An LLM-powered agent specialized in writing Ruby and InSpec code. It takes a generated baseline stub and fills in the control logic based on the details provided in the DISA STIG manual (XML/HTML).  
  * **Inputs:** Path to the InSpec stub directory, path to the DISA STIG manual.  
  * **Outputs:** The InSpec baseline with implemented control code.  
* **QA & Remediation Agent (qa\_agent.py)**  
  * **Responsibility:** An autonomous agent that manages the entire testing and fixing loop.  
  * **Inputs:** Path to the InSpec baseline to be tested.  
  * **Outputs:** A fully tested and corrected InSpec baseline.

## **III. The Tool Layer: MCP Services**

These are the "hands" of the operation. Each tool will be a standalone, network-callable MCP server, promoting modularity and independent development/testing. Each service should implement structured logging for observability.

* **DISA STIG Tool (tools/disa\_stig\_tool.py)**:  
  * **Purpose:** Fetches and extracts STIGs from the DISA website. [https://public.cyber.mil/stigs/downloads/](https://public.cyber.mil/stigs/downloads/)  
  * **MCP Tool Name:** fetch\_disa\_stig  
  * **Returns:** A JSON object containing the local path to the extracted XCCDF file and the manual file.  
* **MITRE Baseline Tool (tools/mitre\_baseline\_tool.py):**  
  * **Purpose:** Finds and clones existing baselines from GitHub by testing stub name to path. [https://github.com/mitre/redhat-enterprise-linux-9-stig-baseline](https://github.com/mitre/redhat-enterprise-linux-9-stig-baseline)  
  * **MCP Tool Name:** find\_mitre\_baseline  
  * **Returns:** A JSON object with the local path to the cloned repository, or a status: "not\_found" message.  
* **SAF Generator Tool (tools/saf\_generator\_tool.py):**  
  * **Purpose:** Wraps the saf CLI to create InSpec stubs. [https://saf-cli.mitre.org/](https://saf-cli.mitre.org/)  
  * **MCP Tool Name:** generate\_saf\_stub  
  * **Returns:** A JSON object with the path to the newly created baseline stub directory.  
* **Docker Tool (tools/docker\_tool.py):**  
  * **Purpose:** Manages Docker images and containers for the test environment. [https://hub.docker.com/search](https://hub.docker.com/search)  
  * **MCP Tool Name:** fetch\_docker\_image  
  * **Returns:** A JSON object with the name and tag of the pulled Docker image.  
* **InSpec Runner Tool (tools/inspec\_runner\_tool.py):**  
  * **Purpose:** Executes InSpec tests against a target and returns results.  
  * **MCP Tool Name:** run\_inspec\_tests  
  * **Returns:** The full test results in JSON format.  
* **Memory Tool (tools/memory\_tool.py):**  
  * **Purpose:** Provides an interface to the long-term memory of the system. [https://docs.trychroma.com/docs/overview/getting-started](https://docs.trychroma.com/docs/overview/getting-started)  
  * **MCP Tool Name:** manage\_baseline\_memory  
  * **Functions:**  
    * add\_to\_memory(baseline\_path): Parses a validated baseline and stores its controls in the knowledge store.  
    * query\_memory(control\_description): Searches the knowledge store for relevant, previously implemented InSpec controls.

## **IV. Memory & Knowledge Store**

* **ChromaDB Service:**  
  * **Responsibility:** Provides a persistent vector database that allows for semantic search of InSpec control examples.  
  * **Deployment:** Runs as a dedicated service in the docker-compose.yml stack, managed exclusively by the memory\_tool.

## **V. Project Structure & Setup**

```bash
❯ tree --dirsfirst --sort=name saf-stig-generator 
saf-stig-generator
├── agents
│   ├── coding_agent.py
│   ├── orchestrator_agent.py
│   └── qa_agent.py
├── artifacts
│   ├── downloads
│   └── generated
├── config
│   ├── development.env
│   └── production.env
├── notes
│   └── design.md
├── tests
│   ├── agents
│   │   └── test_orchestrator_workflow.py
│   └── tools
│       └── test_disa_stig_tool.py
├── tools
│   ├── disa_stig_tool.py
│   ├── docker_tool.py
│   ├── inspec_runner_tool.py
│   ├── memory_tool.py
│   ├── mitre_baseline_tool.py
│   └── saf_generator_tool.py
├── docker-compose.yml
├── LICENSE
├── pyproject.toml
└── README.md
```

## **VI. Development & Implementation Roadmap**

* **Phase 1: Tool Development & Unit Testing**  
  * Implement and write unit tests for each of the five MCP services. Ensure each tool is robust and reliable in isolation.  
* **Phase 2: Agent Scaffolding & Integration Testing**  
  * Build the basic structure for the Orchestrator, Coding, and QA agents.  
  * Develop the Coding Agent's core logic for implementing a single, simple control.  
  * Write integration tests for the Orchestrator to verify it can correctly call the mock MCP tools and handle their responses.  
* **Phase 3: Full Workflow Integration**  
  * Implement the complete logic for the Orchestrator Agent to manage the end-to-end process.  
  * Integrate the real Coding Agent and QA Agent.  
  * Implement the QA Agent's full testing and remediation loop.  
* **Phase 4: End-to-End Testing & Refinement**  
  * Run the entire system with a simple STIG.  
  * Evaluate agent performance, refine prompts, and improve decision-making logic.  
  * Add comprehensive error handling and harden the system for reliability.

## **VII. Testing Strategy**

A multi-layered testing approach is essential for ensuring the reliability of an agentic system.

* **Unit Tests (tests/tools/)**:  
  * **Focus:** Test the internal logic of each MCP tool in isolation.  
  * **Example:** For disa\_stig\_tool, a unit test would mock the requests.get call and provide fake HTML content to verify that the link parsing and file extraction logic works correctly. This is done without making any actual network calls.  
* **Integration Tests (tests/agents/)**:  
  * **Focus:** Test the agent's ability to interact with the tool layer and make decisions.  
  * **Example:** An integration test for the Orchestrator Agent would involve running the agent against mock MCP services. These mocks would return predefined successful or failure responses, allowing you to verify that the agent follows the correct logical path (e.g., proceeds to stub generation when the mitre\_baseline\_tool returns "not found").  
* **Agent Evaluation (E2E)**:  
  * **Focus:** Assess the quality and performance of the LLM-powered agents (Coding and QA) on a "golden dataset."  
  * Process:  
    a. Create a set of representative target products (e.g., RHEL 9, Windows Server 2022).  
    b. Run the entire system for each target.  
    c. Evaluate the final generated baseline against a known-good, manually created baseline.  
    d. Track metrics like code correctness, number of remediation loops, and overall success rate. This process is repeated whenever a core prompt or agent model is updated to prevent regressions.

## **VIII. Deployment & Operational Considerations**

* **Containerization & Orchestration:**  
  * **docker-compose.yml**: This file will define all the MCP tool services, including ChromaDB. This allows for one-command startup of the entire tool ecosystem for both local development and deployment.  
  * Each tool will have its own Dockerfile to create a lightweight, portable container image.  
* **Configuration Management (config/)**:  
  * Environment variables will be used to manage configuration. Files like development.env and production.env will store settings such as:  
    * Endpoints for each MCP service.  
    * API keys (e.g., for GitHub).  
    * Paths for artifact storage.  
  * The agents and tools will load their configuration from these environment files, ensuring a clean separation between code and configuration.  
* **Running the Agents:**  
  * The agents themselves can be run as long-lived processes (e.g., in their own containers) that listen for tasks, or as batch jobs triggered by an external event or a user request. For this system, a triggered job model is likely most appropriate.  
* **Artifact Storage:**  
  * **Local:** The artifacts/ directory is suitable for local development.  
  * **Production:** In a production environment, downloaded STIGs, generated baselines, and logs should be stored in a more persistent and scalable location, such as a Google Cloud Storage bucket or a dedicated file server. The storage location would be configured via environment variables.
