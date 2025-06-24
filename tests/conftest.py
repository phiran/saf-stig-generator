"""
Shared pytest configuration and fixtures for testing MCP tools.
"""

import asyncio

# Add the project root to the Python path
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import respx

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_artifacts_dir():
    """Create temporary artifacts directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_context():
    """Mock MCP context for testing."""
    context = AsyncMock()
    context.info = AsyncMock()
    context.error = AsyncMock()
    context.debug = AsyncMock()
    return context


@pytest.fixture
def sample_stig_data():
    """Sample STIG XCCDF data for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<Benchmark xmlns="http://checklists.nist.gov/xccdf/1.1"
           id="RHEL_9_STIG">
    <title>Red Hat Enterprise Linux 9 Security Technical Implementation Guide</title>
    <Group id="V-230222">
        <title>RHEL 9 must be vendor supported</title>
        <Rule id="SV-230222r627750_rule" severity="high">
            <title>The RHEL 9 operating system must be a vendor-supported release.</title>
        </Rule>
    </Group>
</Benchmark>"""


@pytest.fixture
def sample_inspec_control():
    """Sample InSpec control for testing."""
    return """
control 'V-230222' do
  title 'The RHEL 9 operating system must be a vendor-supported release.'
  desc 'An operating system release that is not supported by the vendor...'
  impact 1.0
  tag severity: 'high'
  tag gtitle: 'SRG-OS-000480-GPOS-00227'
  tag gid: 'V-230222'
  tag rid: 'SV-230222r627750_rule'
  tag stig_id: 'RHEL-09-211010'
  tag fix_id: 'F-32866r567462_fix'
  tag cci: ['CCI-000366']
  tag nist: ['CM-6 b']
  tag 'host'

  describe 'The operating system' do
    it { should be_supported }
  end
end
"""


@pytest.fixture
def mock_github_api_response():
    """Mock GitHub API response for baseline search."""
    return {
        "items": [
            {
                "name": "redhat-enterprise-linux-9-stig-baseline",
                "html_url": "https://github.com/mitre/redhat-enterprise-linux-9-stig-baseline",
                "clone_url": "https://github.com/mitre/redhat-enterprise-linux-9-stig-baseline.git",
                "description": "MITRE InSpec Profile for Red Hat Enterprise Linux 9 STIG",
            }
        ]
    }


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# HTML fixtures for mocking web responses
@pytest.fixture
def disa_downloads_page():
    """Mock DISA STIG downloads page HTML."""
    return """
    <html>
        <body>
            <div>
                <a href="/stigs/zip/U_RHEL_9_V1R1_STIG.zip">
                    Red Hat Enterprise Linux 9 STIG - Ver 1, Rel 1
                </a>
                <a href="/stigs/zip/U_Windows_2022_V1R1_STIG.zip">
                    Windows Server 2022 STIG - Ver 1, Rel 1
                </a>
                <a href="/stigs/zip/U_Ubuntu_22-04_LTS_V1R1_STIG.zip">
                    Ubuntu 22.04 LTS STIG - Ver 1, Rel 1
                </a>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def empty_disa_page():
    """Mock empty DISA downloads page."""
    return "<html><body><div>No STIGs found</div></body></html>"


@pytest.fixture
def mock_http_api():
    """Fixture for mocking HTTP requests using respx."""
    with respx.mock:
        yield


@pytest.fixture
def mock_chromadb_collection():
    """Mock ChromaDB collection for memory tool tests."""
    from unittest.mock import MagicMock

    collection = MagicMock()
    collection.add = MagicMock()
    collection.query = MagicMock()
    return collection


@pytest.fixture
def mock_docker_client():
    """Mock Docker client for docker tool tests."""
    from unittest.mock import MagicMock

    client = MagicMock()
    client.ping.return_value = True
    client.images = MagicMock()
    client.images.pull = MagicMock()
    return client
