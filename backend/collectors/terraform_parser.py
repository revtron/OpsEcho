import logging
import json
import re
from typing import Dict, Any, List, Optional

# Common Terraform error patterns
TERRAFORM_ERROR_PATTERNS = [
    (r"Error: (.+)$", "error"),
    (r"Error applying", "apply_error"),
    (r"Error acquiring the state lock", "state_lock_error"),
    (r"Error refreshing state", "state_refresh_error"),
    (r"timeout while waiting for state to become", "timeout"),
    (r"Provider .+ had an error", "provider_error"),
    (r"Resource .+ has a problem", "resource_error"),
    (r"status code: [45]\d\d", "http_error"),
    (r"context deadline exceeded", "timeout"),
    (r"no such host", "dns_error"),
    (r"connection refused", "connection_error"),
    (r"failed to create", "create_failure"),
    (r"failed to delete", "delete_failure"),
    (r"failed to update", "update_failure"),
    (r"Invalid or unknown key", "syntax_error"),
    (r"Unsupported argument", "syntax_error"),
    (r"Missing required argument", "syntax_error"),
]

class TerraformParser:
    def __init__(self):
        logging.info("Terraform parser initialized")

    def parse_plan(self, plan_output: str) -> Dict[str, Any]:
        """Parse Terraform plan output to extract changes."""
        changes = {
            "create": [],
            "update": [],
            "delete": [],
            "resources": {},
        }

        # Check for errors in plan output
        errors = self._detect_errors(plan_output)
        if errors:
            return {
                "changes": changes,
                "error": errors[0]["message"],
                "errors": errors,
            }

        create_pattern = r"# (\S+) will be created"
        update_pattern = r"# (\S+) will be updated in-place"
        delete_pattern = r"# (\S+) will be destroyed"

        for match in re.finditer(create_pattern, plan_output):
            changes["create"].append(match.group(1))

        for match in re.finditer(update_pattern, plan_output):
            changes["update"].append(match.group(1))

        for match in re.finditer(delete_pattern, plan_output):
            changes["delete"].append(match.group(1))

        resource_pattern = r'resource\s+"(\S+)"\s+"(\S+)"'
        for match in re.finditer(resource_pattern, plan_output):
            resource_type, resource_name = match.groups()
            key = f"{resource_type}.{resource_name}"
            if key not in changes["resources"]:
                changes["resources"][key] = {
                    "type": resource_type,
                    "name": resource_name,
                    "changes": {},
                }

        return changes

    def parse_apply(self, apply_output: str) -> Dict[str, Any]:
        """Parse Terraform apply output."""
        # Check for errors first
        errors = self._detect_errors(apply_output)
        if errors:
            return {
                "changes": {"create": [], "update": [], "delete": [], "resources": {}},
                "error": errors[0]["message"],
                "errors": errors,
                "apply_status": "failed",
            }

        changes = self.parse_plan(apply_output)
        changes["apply_status"] = "success"

        # Count applied resources
        apply_pattern = r"Apply complete! Resources: (\d+) added, (\d+) changed, (\d+) destroyed"
        match = re.search(apply_pattern, apply_output)
        if match:
            changes["applied"] = {
                "added": int(match.group(1)),
                "changed": int(match.group(2)),
                "destroyed": int(match.group(3)),
            }

        return changes

    def _detect_errors(self, output: str) -> List[Dict[str, str]]:
        """Detect errors in Terraform output."""
        errors = []
        for pattern, error_type in TERRAFORM_ERROR_PATTERNS:
            for match in re.finditer(pattern, output, re.MULTILINE):
                message = match.group(1) if match.lastindex else match.group(0)
                errors.append({
                    "type": error_type,
                    "message": message.strip(),
                })
        return errors

    def extract_resource_changes(self, tfstate: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract changes from Terraform state (for drift detection)."""
        changes = []
        resources = tfstate.get("resources", [])
        for resource in resources:
            pass
        return changes


if __name__ == "__main__":
    parser = TerraformParser()
    sample_plan = """
    # aws_instance.web will be created
    # aws_security_group.web will be created
    # aws_instance.db will be updated in-place
    # aws_s3_bucket.logs will be destroyed
    """
    print(json.dumps(parser.parse_plan(sample_plan), indent=2))

    sample_error = """
    Error: Error creating S3 bucket: AccessDenied: Access Denied
    """
    print("\nError parsing:")
    print(json.dumps(parser.parse_plan(sample_error), indent=2))
