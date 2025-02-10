"""Data transfer object for Kubernetes commands."""
from pydantic import BaseModel, field_validator


class KubernetesCommand(BaseModel):
    """Data transfer object for Kubernetes commands."""
    command: str

    @field_validator("command")
    @classmethod
    def validate_command(cls, value:str)-> str:
        """Validate the command."""
        if not value.startswith("kubectl"):
            raise ValueError("Command must start with 'kubectl'")
        return value.strip().lower()
