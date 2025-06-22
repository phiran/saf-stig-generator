import os
import shutil

import git

from agents.saf_stig_generator.services.memory.tool import manage_baseline_memory

# List of high-quality baseline repositories to learn from
# All of these are from the MITRE GitHub org:
# https://github.com/search?q=org%3Amitre+stig+in%3Aname&type=repositories
PRETRAIN_REPOS = [
    "https://github.com/mitre/juniper-srx-services-gateway-ndm-stig-baseline",
    "https://github.com/mitre/aws-rds-crunchy-data-postgresql-16-stig-baseline",
    "https://github.com/mitre/redhat-enterprise-linux-8-stig-baseline",
    "https://github.com/mitre/microsoft-windows-10-stig-baseline",
    "https://github.com/mitre/oracle-database-12c-stig-baseline",
    "https://github.com/mitre/nginx-stigready-baseline",
    "https://github.com/mitre/oracle-mysql-8-stig-baseline",
    "https://github.com/mitre/apache-tomcat-9.x-stig-baseline",
]

TEMP_CLONE_DIR = "./artifacts/temp_pretrain"


def run_pretraining():
    """
    Clones repositories and uses the memory_tool to ingest them.
    """
    if os.path.exists(TEMP_CLONE_DIR):
        print(f"Removing existing temp directory: {TEMP_CLONE_DIR}")
        shutil.rmtree(TEMP_CLONE_DIR)
    os.makedirs(TEMP_CLONE_DIR)

    print("--- Starting Pre-training Ingestion ---")

    for repo_url in PRETRAIN_REPOS:
        try:
            repo_name = repo_url.split("/")[-1]
            clone_path = os.path.join(TEMP_CLONE_DIR, repo_name)
            print(f"\nCloning {repo_url} into {clone_path}...")
            git.Repo.clone_from(repo_url, clone_path)

            # Now, call the memory tool to ingest this directory
            # We specifically target the 'controls' sub-directory in these repos
            controls_path = os.path.join(clone_path, "controls")
            if os.path.isdir(controls_path):
                result = manage_baseline_memory(
                    action="add", baseline_path=controls_path
                )
                print(result["message"])
            else:
                print(
                    f"[Warning] No 'controls' directory found in {repo_name}. Skipping ingestion."
                )

        except Exception as e:
            print(f"Failed to process {repo_url}: {e}")

    # Clean up the temporary clones
    print("\nCleaning up temporary files...")
    shutil.rmtree(TEMP_CLONE_DIR)
    print("--- Pre-training Complete ---")


if __name__ == "__main__":
    # To run this script: python pretrain.py
    run_pretraining()
