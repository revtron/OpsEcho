import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class EC2HealthCollector:
    """
    Collects EC2 instance health information.
    In production, this uses boto3 to query AWS EC2 APIs and CloudWatch metrics.
    For demo/offline mode, it returns simulated data.
    """

    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.ec2_client = None
        self.cloudwatch_client = None
        self._init_aws_clients()

    def _init_aws_clients(self):
        try:
            import boto3
            self.ec2_client = boto3.client("ec2", region_name=self.region)
            self.cloudwatch_client = boto3.client("cloudwatch", region_name=self.region)
            logger.info(f"EC2HealthCollector initialized for region {self.region}")
        except Exception as e:
            logger.warning(f"Could not initialize AWS clients: {e}. Using demo mode.")

    def _has_aws_access(self) -> bool:
        if self.ec2_client is None:
            return False
        try:
            self.ec2_client.describe_regions(MaxResults=1)
            return True
        except Exception:
            logger.warning("AWS credentials not configured or no network access. Using demo mode.")
            return False

    def get_instance_health(self) -> List[Dict[str, Any]]:
        """Get health status for all EC2 instances."""
        if self._has_aws_access():
            return self._fetch_real_instance_health()
        return self._demo_instance_health()

    def _fetch_real_instance_health(self) -> List[Dict[str, Any]]:
        """Fetch real EC2 health from AWS."""
        instances = []
        try:
            response = self.ec2_client.describe_instances()
            for reservation in response.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    inst_id = instance.get("InstanceId", "unknown")
                    name_tag = "unknown"
                    if instance.get("Tags"):
                        for tag in instance["Tags"]:
                            if tag["Key"] == "Name":
                                name_tag = tag["Value"]
                                break

                    instance_info = {
                        "instance_id": inst_id,
                        "name": name_tag,
                        "instance_type": instance.get("InstanceType", "unknown"),
                        "state": instance.get("State", {}).get("Name", "unknown"),
                        "launch_time": instance.get("LaunchTime").isoformat() if instance.get("LaunchTime") else None,
                        "region": self.region,
                        "private_ip": instance.get("PrivateIpAddress", ""),
                        "public_ip": instance.get("PublicIpAddress", ""),
                        "vpc_id": instance.get("VpcId", ""),
                        "subnet_id": instance.get("SubnetId", ""),
                    }

                    try:
                        status_response = self.ec2_client.describe_instance_status(
                            InstanceIds=[inst_id]
                        )
                        if status_response.get("InstanceStatuses"):
                            status = status_response["InstanceStatuses"][0]
                            instance_info["status_check"] = status.get(
                                "InstanceStatus", {}
                            ).get("Status", "unknown")
                            instance_info["system_status_check"] = status.get(
                                "SystemStatus", {}
                            ).get("Status", "unknown")
                            instance_info["events"] = [
                                {
                                    "code": e.get("Code", ""),
                                    "description": e.get("Description", ""),
                                }
                                for e in status.get("Events", [])
                            ]
                        else:
                            instance_info["status_check"] = "initializing"
                            instance_info["system_status_check"] = "initializing"
                            instance_info["events"] = []
                    except Exception:
                        instance_info["status_check"] = "unknown"
                        instance_info["system_status_check"] = "unknown"
                        instance_info["events"] = []

                    instances.append(instance_info)
        except Exception as e:
            logger.error(f"Error fetching EC2 health: {e}")
        return instances

    def _demo_instance_health(self) -> List[Dict[str, Any]]:
        """Generate realistic demo EC2 instances."""
        now = datetime.now(timezone.utc)
        return [
            {
                "instance_id": "i-0a1b2c3d4e5f6a7b8",
                "name": "web-server-prod-01",
                "instance_type": "t3.large",
                "state": "running",
                "status_check": "ok",
                "system_status_check": "ok",
                "launch_time": now.isoformat(),
                "region": self.region,
                "private_ip": "10.0.1.12",
                "public_ip": "52.1.2.3",
                "vpc_id": "vpc-0a1b2c3d",
                "subnet_id": "subnet-0a1b2c3d",
                "events": [],
            },
            {
                "instance_id": "i-0b2c3d4e5f6a7b8c9",
                "name": "web-server-prod-02",
                "instance_type": "t3.large",
                "state": "running",
                "status_check": "ok",
                "system_status_check": "ok",
                "launch_time": now.isoformat(),
                "region": self.region,
                "private_ip": "10.0.1.13",
                "public_ip": "52.1.2.4",
                "vpc_id": "vpc-0a1b2c3d",
                "subnet_id": "subnet-0a1b2c3d",
                "events": [],
            },
            {
                "instance_id": "i-0c3d4e5f6a7b8c9d0",
                "name": "api-server-prod-01",
                "instance_type": "t3.xlarge",
                "state": "running",
                "status_check": "impaired",
                "system_status_check": "ok",
                "launch_time": now.isoformat(),
                "region": self.region,
                "private_ip": "10.0.2.10",
                "public_ip": "52.1.2.10",
                "vpc_id": "vpc-0a1b2c3d",
                "subnet_id": "subnet-0a2b3c4d",
                "events": [
                    {"code": "instance-retirement", "description": "Instance scheduled for retirement"}
                ],
            },
            {
                "instance_id": "i-0d4e5f6a7b8c9d0e1",
                "name": "db-replica-01",
                "instance_type": "r5.large",
                "state": "running",
                "status_check": "degraded",
                "system_status_check": "degraded",
                "launch_time": now.isoformat(),
                "region": self.region,
                "private_ip": "10.0.3.5",
                "public_ip": "",
                "vpc_id": "vpc-0a1b2c3d",
                "subnet_id": "subnet-0a3b4c5d",
                "events": [],
            },
            {
                "instance_id": "i-0e5f6a7b8c9d0e1f2",
                "name": "batch-worker-01",
                "instance_type": "c5.2xlarge",
                "state": "stopped",
                "status_check": "unknown",
                "system_status_check": "unknown",
                "launch_time": now.isoformat(),
                "region": self.region,
                "private_ip": "10.0.4.20",
                "public_ip": "",
                "vpc_id": "vpc-0a1b2c3d",
                "subnet_id": "subnet-0a4b5c6d",
                "events": [],
            },
            {
                "instance_id": "i-0f6a7b8c9d0e1f2a3",
                "name": "redis-cache-01",
                "instance_type": "r6g.large",
                "state": "running",
                "status_check": "insufficient-data",
                "system_status_check": "ok",
                "launch_time": now.isoformat(),
                "region": self.region,
                "private_ip": "10.0.5.15",
                "public_ip": "",
                "vpc_id": "vpc-0a1b2c3d",
                "subnet_id": "subnet-0a5b6c7d",
                "events": [],
            },
        ]


if __name__ == "__main__":
    collector = EC2HealthCollector()
    instances = collector.get_instance_health()
    import json
    print(json.dumps(instances, indent=2))
