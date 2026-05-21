import logging
import json
from typing import Dict, Any
import git
from github import Github
import os
from datetime import datetime

class GitWebhook:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Initialize GitHub client if token is available
        self.github_token = os.getenv("GITHUB_TOKEN")
        if self.github_token:
            self.g = Github(self.github_token)
        else:
            self.g = None
            self.logger.warning("GitHub token not provided, GitHub API features will be limited")

    def process_push_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a Git push webhook event.
        """
        try:
            ref = payload.get("ref", "")
            # Extract branch name from ref (e.g., refs/heads/main -> main)
            branch = ref.split("/")[-1] if ref.startswith("refs/heads/") else ref
            
            commits = payload.get("commits", [])
            processed_commits = []
            
            for commit in commits:
                processed_commit = {
                    "id": commit.get("id"),
                    "message": commit.get("message"),
                    "timestamp": commit.get("timestamp"),
                    "author": commit.get("author", {}).get("name"),
                    "url": commit.get("url"),
                    "added": commit.get("added", []),
                    "removed": commit.get("removed", []),
                    "modified": commit.get("modified", [])
                }
                processed_commits.append(processed_commit)
            
            event_data = {
                "event_type": "push",
                "ref": ref,
                "branch": branch,
                "repository": payload.get("repository", {}),
                "commits": processed_commits,
                "total_commits": len(commits),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "git"
            }
            
            return event_data
        except Exception as e:
            self.logger.error(f"Error processing push event: {e}")
            return {}

    def process_pull_request_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a Git pull request webhook event.
        """
        try:
            action = payload.get("action")
            pr = payload.get("pull_request", {})
            
            event_data = {
                "event_type": "pull_request",
                "action": action,
                "pull_request": {
                    "id": pr.get("id"),
                    "number": pr.get("number"),
                    "title": pr.get("title"),
                    "state": pr.get("state"),
                    "merged": pr.get("merged"),
                    "merge_commit_sha": pr.get("merge_commit_sha"),
                    "user": pr.get("user", {}).get("login"),
                    "created_at": pr.get("created_at"),
                    "updated_at": pr.get("updated_at"),
                    "closed_at": pr.get("closed_at"),
                    "merged_at": pr.get("merged_at")
                },
                "repository": payload.get("repository", {}),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "git"
            }
            
            return event_data
        except Exception as e:
            self.logger.error(f"Error processing pull request event: {e}")
            return {}

    def get_recent_commits(self, repo_path: str, since: str = None) -> list:
        """
        Get recent commits from a local git repository.
        """
        try:
            repo = git.Repo(repo_path)
            if since:
                commits = repo.iter_commits(since=since)
            else:
                commits = repo.iter_commits(max_count=10)  # Last 10 commits
            
            commit_list = []
            for commit in commits:
                commit_list.append({
                    "id": commit.hexsha,
                    "message": commit.message,
                    "author": commit.author.name,
                    "timestamp": commit.authored_datetime.isoformat(),
                    "files": [item.a_path for item in commit.diff(commit.parents[0]) if commit.parents] if commit.parents else []
                })
            
            return commit_list
        except Exception as e:
            self.logger.error(f"Error getting recent commits: {e}")
            return []

    def get_file_changes(self, repo_path: str, commit_sha: str) -> dict:
        """
        Get file changes for a specific commit.
        """
        try:
            repo = git.Repo(repo_path)
            commit = repo.commit(commit_sha)
            
            files_changed = []
            for item in commit.diff(commit.parents[0]) if commit.parents else commit.diff():
                files_changed.append({
                    "file": item.a_path or item.b_path,
                    "change_type": item.change_type,  # 'A', 'D', 'M', 'R'
                    "added_lines": item.a_blob.size if item.change_type == 'A' else 0,
                    "deleted_lines": item.b_blob.size if item.change_type == 'D' else 0
                })
            
            return {
                "commit": commit.hexsha,
                "message": commit.message,
                "author": commit.author.name,
                "timestamp": commit.authored_datetime.isoformat(),
                "files_changed": files_changed
            }
        except Exception as e:
            self.logger.error(f"Error getting file changes: {e}")
            return {}

# For testing
if __name__ == "__main__":
    webhook = GitWebhook()
    # Example push payload
    sample_payload = {
        "ref": "refs/heads/main",
        "repository": {
            "id": 123456,
            "name": "my-app",
            "full_name": "user/my-app"
        },
        "commits": [
            {
                "id": "abc123",
                "message": "Fix bug in payment processing",
                "timestamp": "2024-01-01T12:00:00Z",
                "author": {"name": "John Doe"},
                "url": "https://github.com/user/my-app/commit/abc123",
                "added": [],
                "removed": [],
                "modified": ["src/payment.py"]
            }
        ]
    }
    print(json.dumps(webhook.process_push_event(sample_payload), indent=2))