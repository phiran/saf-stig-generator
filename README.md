# MITRE SAF STIG Baseline Generation System

This project is an autonomous system built using the Google Agent Development Kit (ADK). Its purpose is to automate the entire lifecycle of generating, implementing, and validating security compliance baselines based on DISA STIGs and the MITRE SAF framework.

## Overview

The system uses a multi-agent architecture where an **Orchestrator Agent** manages a workflow executed by specialized agents (like a **Coding Agent** and **QA Agent**) and a suite of modular MCP Tools.

## Getting Started

1. **Install `uv`:** `pip install uv`
2. **Create virtual environment:** `uv venv`
3. **Activate environment:** `source .venv/bin/activate`
4. **Install dependencies:** `uv pip install -e .`
5. **Run services:** `docker-compose up --build`

## Code inspiration

- [Google adk-samples](https://github.com/google/adk-samples/tree/main/python/agents/llm-auditor)
- [Google a2a-samples](https://github.com/google-a2a/a2a-samples)
