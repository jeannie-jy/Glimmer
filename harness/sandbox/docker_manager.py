"""Docker-based sandbox manager for isolated Agent execution."""
import os
import asyncio
from dataclasses import dataclass

DOCKER_HOST = os.environ.get("DOCKER_HOST", "unix:///var/run/docker.sock")
SANDBOX_IMAGE = os.environ.get("SANDBOX_IMAGE", "glimmer-sandbox:latest")
WORKSPACE_ROOT = os.environ.get("WORKSPACE_ROOT", "/workspace")


@dataclass
class ExecResult:
    exit_code: int
    stdout: str
    stderr: str


class DockerManager:
    """Manages lifecycle of sandbox containers for Agent sessions."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import docker
            self._client = docker.DockerClient(base_url=DOCKER_HOST)
        return self._client

    async def create(self, user_id: str, session_id: str) -> str:
        """Create and start a sandbox container. Returns container_id."""
        container_name = f"agent-{session_id[:12]}"
        user_workspace = os.path.join(WORKSPACE_ROOT, user_id)
        os.makedirs(user_workspace, exist_ok=True)

        container = await asyncio.to_thread(
            self.client.containers.run,
            image=SANDBOX_IMAGE,
            command=["sleep", "infinity"],
            name=container_name,
            network_mode="none",
            mem_limit="512m",
            nano_cpus=1_000_000_000,
            pids_limit=100,
            volumes={user_workspace: {"bind": "/workspace", "mode": "rw"}},
            remove=True,
            detach=True,
        )
        return container.id

    async def exec(self, container_id: str, cmd: str, timeout: int = 600) -> ExecResult:
        """Execute a command inside the container and return result."""
        async def _run():
            container = self.client.containers.get(container_id)
            exit_code, output = container.exec_run(
                ["sh", "-c", cmd],
                stdout=True,
                stderr=True,
            )
            return ExecResult(
                exit_code=exit_code,
                stdout=output[0].decode("utf-8", errors="replace") if output[0] else "",
                stderr=output[1].decode("utf-8", errors="replace") if output[1] else "",
            )

        try:
            return await asyncio.wait_for(asyncio.to_thread(_run), timeout=timeout + 5)
        except asyncio.TimeoutError:
            return ExecResult(exit_code=-1, stdout="", stderr="Command timed out")

    async def destroy(self, container_id: str) -> None:
        """Stop and remove a container."""
        try:
            await asyncio.to_thread(
                lambda: self.client.containers.get(container_id).kill()
            )
        except Exception:
            pass
