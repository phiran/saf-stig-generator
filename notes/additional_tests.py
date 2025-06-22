# tests/services/test_disa_stig_tooltest_disa_stig_tool.py

import pytest
from unittest.mock import patch, mock_open, MagicMock
from agents.services.disa_stig_tool.disa_stig_tool import fetch_disa_stig, DisaStigTool
import zipfile
import io


# Existing test from user
def test_fetch_disa_stig_tool():
    tool = DisaStigTool()
    assert tool.name == "DisaStigTool"


# New tests for disa_stig_tool
@patch("requests.get")
def test_fetch_disa_stig_success(mock_get):
    """
    Test the successful download and extraction of a STIG file.
    """
    # Mock the response from requests.get
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Create a fake zip file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("U_RHEL_9_V1R1_STIG_SCAP_1-2_Benchmark.xml", "test xccdf data")
        zf.writestr("U_RHEL_9_V1R1_STIG_Manual.html", "test manual data")
    mock_response.content = zip_buffer.getvalue()
    mock_get.return_value = mock_response

    # Mock file system operations
    with (
        patch("os.makedirs"),
        patch("builtins.open", mock_open()) as mock_file,
        patch("zipfile.ZipFile") as mock_zip,
    ):

        # Configure the mock zip file to simulate our in-memory one
        mock_zip.return_value.__enter__.return_value.namelist.return_value = [
            "U_RHEL_9_V1R1_STIG_SCAP_1-2_Benchmark.xml",
            "U_RHEL_9_V1R1_STIG_Manual.html",
        ]

        # Call the function
        result = fetch_disa_stig("Red Hat Enterprise Linux 9")

        # Assertions
        mock_get.assert_called_once()
        assert "downloads/Red_Hat_Enterprise_Linux_9" in result["xccdf_path"]
        assert "U_RHEL_9_V1R1_STIG_SCAP_1-2_Benchmark.xml" in result["xccdf_path"]
        assert "downloads/Red_Hat_Enterprise_Linux_9" in result["manual_path"]
        assert "U_RHEL_9_V1R1_STIG_Manual.html" in result["manual_path"]
        assert result["status"] == "success"


@patch("requests.get")
def test_fetch_disa_stig_download_failed(mock_get):
    """
    Test how the tool handles a failed download (e.g., 404 error).
    """
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    result = fetch_disa_stig("Non Existent Product")

    assert result["status"] == "error"
    assert "Failed to download" in result["message"]


@patch("requests.get")
def test_fetch_disa_stig_no_stig_found(mock_get):
    """
    Test the scenario where the download is successful but no STIG files are found in the zip.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("some_other_file.txt", "data")
    mock_response.content = zip_buffer.getvalue()
    mock_get.return_value = mock_response

    with (
        patch("os.makedirs"),
        patch("builtins.open", mock_open()),
        patch("zipfile.ZipFile") as mock_zip,
    ):

        mock_zip.return_value.__enter__.return_value.namelist.return_value = [
            "some_other_file.txt"
        ]
        result = fetch_disa_stig("Product with no STIG")

        assert result["status"] == "error"
        assert "Could not find XCCDF" in result["message"]


# tests/services/test_mitre_baseline_tool.py

import pytest
from unittest.mock import patch
from agents.services.mitre_baseline_tool.mitre_baseline_tool import find_mitre_baseline


@patch("git.Repo.clone_from")
def test_find_mitre_baseline_exists(mock_clone_from):
    """
    Test finding an existing MITRE baseline.
    """
    product_name = "Red Hat Enterprise Linux 9"
    expected_repo_url = (
        "https://github.com/mitre/redhat-enterprise-linux-9-stig-baseline"
    )
    expected_path = "downloads/baselines/redhat-enterprise-linux-9-stig-baseline"

    result = find_mitre_baseline(product_name)

    mock_clone_from.assert_called_with(expected_repo_url, expected_path)
    assert result["status"] == "found"
    assert result["path"] == expected_path


@patch("git.Repo.clone_from", side_effect=Exception("Git command failed"))
def test_find_mitre_baseline_not_found(mock_clone_from):
    """
    Test when the baseline repository does not exist and git clone fails.
    """
    product_name = "Non Existent Baseline"
    result = find_mitre_baseline(product_name)

    assert result["status"] == "not_found"
    assert "could not be found" in result["message"]


# tests/services/test_saf_generator_tool.py

import pytest
from unittest.mock import patch, MagicMock
from agents.services.saf_generator_tool.saf_generator_tool import generate_saf_stub


@patch("subprocess.run")
def test_generate_saf_stub_success(mock_subprocess_run):
    """
    Test successful generation of an InSpec stub using the saf CLI.
    """
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = "Successfully generated profile"
    mock_process.stderr = ""
    mock_subprocess_run.return_value = mock_process

    xccdf_path = "path/to/some.xml"
    output_dir = "generated/stubs"
    result = generate_saf_stub(xccdf_path, output_dir)

    assert result["status"] == "success"
    assert result["path"] == output_dir
    mock_subprocess_run.assert_called_once()
    # Check if the command was constructed correctly
    args, _ = mock_subprocess_run.call_args
    assert "saf" in args[0]
    assert "generate" in args[0]
    assert xccdf_path in args[0]
    assert f"--output={output_dir}" in args[0]


@patch("subprocess.run")
def test_generate_saf_stub_failure(mock_subprocess_run):
    """
    Test a failed attempt to generate an InSpec stub.
    """
    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process.stdout = ""
    mock_process.stderr = "Error: Invalid XCCDF file."
    mock_subprocess_run.return_value = mock_process

    result = generate_saf_stub("path/to/invalid.xml", "generated/stubs")

    assert result["status"] == "error"
    assert "Failed to generate SAF stub" in result["message"]
    assert "Error: Invalid XCCDF file." in result["message"]


# tests/services/test_docker_tool.py

import pytest
from unittest.mock import patch, MagicMock
from agents.services.docker_tool.docker_tool import fetch_docker_image


@patch("docker.from_env")
def test_fetch_docker_image_success(mock_from_env):
    """
    Test successfully finding and pulling a Docker image.
    """
    mock_docker_client = MagicMock()
    mock_from_env.return_value = mock_docker_client
    # Simulate a successful pull
    mock_image = MagicMock()
    mock_image.tags = ["rhel9:latest"]
    mock_docker_client.images.pull.return_value = mock_image

    product_name = "rhel9"
    result = fetch_docker_image(product_name)

    assert result["status"] == "success"
    assert result["image_name"] == "rhel9:latest"
    mock_docker_client.images.pull.assert_called_with(product_name)


@patch("docker.from_env")
def test_fetch_docker_image_not_found(mock_from_env):
    """
    Test when a specified Docker image cannot be found.
    """
    mock_docker_client = MagicMock()
    mock_from_env.return_value = mock_docker_client
    # Simulate a failure
    mock_docker_client.images.pull.side_effect = Exception("Image not found")

    product_name = "non_existent_image"
    result = fetch_docker_image(product_name)

    assert result["status"] == "error"
    assert "Could not pull Docker image" in result["message"]


# tests/services/test_inspec_runner_tool.py

import pytest
from unittest.mock import patch, MagicMock
from agents.services.inspect_runner_tool.inspec_runner_tool import run_inspec_tests
import json


@patch("subprocess.run")
def test_run_inspec_tests_success(mock_subprocess_run):
    """
    Test a successful InSpec run that returns JSON results.
    """
    mock_process = MagicMock()
    mock_process.returncode = 0  # InSpec can return 0 even with failures
    mock_results = {
        "version": "5.22.29",
        "profiles": [{"status": "loaded"}],
        "statistics": {
            "duration": 0.1,
            "total": 10,
            "passed": {"total": 8},
            "failed": {"total": 2},
        },
    }
    mock_process.stdout = json.dumps(mock_results)
    mock_process.stderr = ""
    mock_subprocess_run.return_value = mock_process

    result = run_inspec_tests("path/to/baseline", "my-container")

    assert result["status"] == "success"
    assert "results" in result
    assert result["results"]["statistics"]["total"] == 10
    # Check command construction
    args, _ = mock_subprocess_run.call_args
    assert "inspec" in args[0]
    assert "exec" in args[0]
    assert "path/to/baseline" in args[0]
    assert "-t" in args[0]
    assert "docker://my-container" in args[0]


@patch("subprocess.run")
def test_run_inspec_tests_command_error(mock_subprocess_run):
    """
    Test when the inspec command itself fails to run.
    """
    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process.stdout = ""
    mock_process.stderr = "InSpec command not found"
    mock_subprocess_run.return_value = mock_process

    result = run_inspec_tests("path/to/baseline", "my-container")

    assert result["status"] == "error"
    assert "InSpec execution failed" in result["message"]
    assert "InSpec command not found" in result["message"]


# tests/services/test_memory_tool.py

import pytest
from unittest.mock import patch, MagicMock
from agents.services.memory_tool.memory_tool import manage_baseline_memory


@patch("chromadb.Client")
def test_memory_tool_add_to_memory(mock_chroma_client):
    """
    Test adding a new baseline control to the memory.
    """
    # Setup mock ChromaDB client and collection
    mock_collection = MagicMock()
    mock_chroma_client.return_value.get_or_create_collection.return_value = (
        mock_collection
    )

    # Mock the file system to read a fake control file
    control_content = """
    control 'V-230222' do
      title 'The RHEL 9 operating system must be a vendor-supported release.'
      desc 'An operating system release...'
      impact 1.0
      describe 'The operating system' do
        it { should be_supported }
      end
    end
    """
    with (
        patch("builtins.open", MagicMock(read_data=control_content)),
        patch("os.walk") as mock_walk,
    ):

        mock_walk.return_value = [("/fake/path", [], ["V-230222.rb"])]

        result = manage_baseline_memory(action="add", baseline_path="/fake/path")

    assert result["status"] == "success"
    assert "Added 1 controls to memory" in result["message"]
    mock_collection.add.assert_called_once()
    # Check the data being added
    _, kwargs = mock_collection.add.call_args
    assert "V-230222" in kwargs["ids"][0]
    assert (
        "The RHEL 9 operating system must be a vendor-supported release."
        in kwargs["documents"][0]
    )


@patch("chromadb.Client")
def test_memory_tool_query_memory(mock_chroma_client):
    """
    Test querying the memory for a similar control.
    """
    mock_collection = MagicMock()
    # Simulate a query result from ChromaDB
    mock_collection.query.return_value = {
        "documents": [["control V-123..."]],
        "metadatas": [[{"source": "RHEL 8 STIG"}]],
        "distances": [[0.123]],
    }
    mock_chroma_client.return_value.get_or_create_collection.return_value = (
        mock_collection
    )

    query_text = "Check if OS is vendor supported"
    result = manage_baseline_memory(action="query", query_text=query_text)

    assert result["status"] == "success"
    assert len(result["results"]) == 1
    assert "control V-123" in result["results"][0]["document"]
    mock_collection.query.assert_called_with(query_texts=[query_text], n_results=5)


@patch("chromadb.Client")
def test_memory_tool_invalid_action(mock_chroma_client):
    """
    Test providing an invalid action to the memory tool.
    """
    result = manage_baseline_memory(action="delete")  # 'delete' is not a valid action
    assert result["status"] == "error"
    assert "Invalid action specified" in result["message"]


tests / services
