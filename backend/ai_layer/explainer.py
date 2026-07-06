import logging
import ollama
from typing import Dict, Any, List
import json
from datetime import datetime

class OperationalExplainer:
    def __init__(self, model_name: str = "mistral"):
        self.logger = logging.getLogger(__name__)
        self.model_name = model_name
        self.logger.info(f"Operational explainer initialized with model: {model_name}")
        
        # Verify model is available
        try:
            ollama.show(model_name)
            self.logger.info(f"Model {model_name} is available")
        except Exception as e:
            self.logger.warning(f"Model {model_name} not found: {e}. Will attempt to pull it.")
            try:
                ollama.pull(model_name)
                self.logger.info(f"Successfully pulled model {model_name}")
            except Exception as pull_error:
                self.logger.error(f"Failed to pull model {model_name}: {pull_error}")

    def generate_summary(self, enriched_event: Dict[Any, Any]) -> str:
        """
        Generate an AI-powered operational summary explaining:
        - what changed
        - probable reason
        - impacted services
        - operational risk
        - historical similarity
        """
        try:
            # Prepare the prompt for the LLM
            prompt = self._build_summary_prompt(enriched_event)
            
            # Generate response using Ollama
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                stream=False,
                keep_alive="10m",
                options={
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "max_tokens": 300
                }
            )
            
            summary = response.get('response', '').strip()
            self.logger.info(f"Generated summary of length {len(summary)}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            return self._generate_fallback_summary(enriched_event)

    def _build_summary_prompt(self, event: Dict[Any, Any]) -> str:
        """
        Build a prompt for the LLM to generate an operational summary.
        """
        # Extract key information
        event_type = event.get("event_type", "unknown")
        source = event.get("source", "unknown")
        timestamp = event.get("timestamp", "unknown")
        
        # Get normalized data
        normalized = event.get("normalized_data", {})
        if isinstance(normalized, str):
            try:
                normalized = json.loads(normalized)
            except:
                normalized = {}
        
        # Get enriched context
        deployment_history = event.get("deployment_history", [])
        related_incidents = event.get("related_incidents", [])
        dependencies = event.get("dependencies", [])
        ownership = event.get("ownership", {})
        historical_patterns = event.get("historical_patterns", {})
        correlations = event.get("correlations", [])
        
        # Build the prompt
        prompt = f"""You are an expert DevOps engineer analyzing infrastructure changes. Based on the following information, provide a concise operational summary that explains:

1. What changed
2. Probable reason for the change
3. Impacted services
4. Operational risk
5. Historical similarity (if any)

INFRASTRUCTURE EVENT:
- Type: {event_type}
- Source: {source}
- Time: {timestamp}
- Details: {json.dumps(normalized, indent=2)}

OPERATIONAL CONTEXT:
- Deployment History: {json.dumps(deployment_history, indent=2) if deployment_history else "None"}
- Related Incidents: {json.dumps(related_incidents, indent=2) if related_incidents else "None"}
- Service Dependencies: {json.dumps(dependencies, indent=2) if dependencies else "None"}
- Service Ownership: {json.dumps(ownership, indent=2) if ownership else "None"}
- Historical Patterns: {json.dumps(historical_patterns, indent=2) if historical_patterns else "None"}
- Infrastructure Correlations: {json.dumps(correlations, indent=2) if correlations else "None"}

Please provide a clear, concise summary focused on operational intelligence. Do not include any preamble or explanation of your reasoning process. Just provide the summary as requested."""

        return prompt

    def _generate_fallback_summary(self, event: Dict[Any, Any]) -> str:
        """
        Generate a fallback summary when the LLM is unavailable.
        """
        event_type = event.get("event_type", "unknown")
        source = event.get("source", "unknown")
        timestamp = event.get("timestamp", "unknown")
        
        normalized = event.get("normalized_data", {})
        if isinstance(normalized, str):
            try:
                normalized = json.loads(normalized)
            except:
                normalized = {}
        
        # Basic fallback summary
        summary = f"""Infrastructure change detected:
- What changed: {event_type} event from {source} at {timestamp}
- Details: {str(normalized)[:200]}{'...' if len(str(normalized)) > 200 else ''}

Operational context has been enriched with deployment history, related incidents, and service dependencies.
For detailed AI-powered analysis, please ensure the Ollama service is running with the mistral model available."""
        
        return summary

    def answer_question(self, question: str, context_events: List[Dict[Any, Any]]) -> str:
        """
        Answer a natural language question about infrastructure history.
        """
        try:
            # Prepare context from events
            context_str = ""
            for i, event in enumerate(context_events[:5]):  # Limit to 5 most relevant events
                normalized = event.get("normalized_data", {})
                if isinstance(normalized, str):
                    try:
                        normalized = json.loads(normalized)
                    except:
                        normalized = {}
                
                context_str += f"Event {i+1}:\n"
                context_str += f"  Type: {event.get('event_type')}\n"
                context_str += f"  Source: {event.get('source')}\n"
                context_str += f"  Time: {event.get('timestamp')}\n"
                context_str += f"  Details: {json.dumps(normalized, indent=2)}\n\n"
            
            prompt = f"""You are an expert DevOps engineer with access to infrastructure history. Answer the following question based on the provided context:

QUESTION: {question}

INFRASTRUCTURE CONTEXT:
{context_str}

Provide a clear, concise answer based only on the information provided. If the context doesn't contain enough information to answer the question, say so clearly."""

            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                stream=False,
                options={
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "max_tokens": 400
                }
            )
            
            answer = response.get('response', '').strip()
            return answer
            
        except Exception as e:
            self.logger.error(f"Error answering question: {e}")
            return f"I'm unable to process your question at the moment due to a technical issue: {str(e)}"

# For testing
if __name__ == "__main__":
    explainer = OperationalExplainer()
    
    # Test event
    test_event = {
        "event_type": "kubernetes",
        "source": "kubernetes",
        "timestamp": "2024-01-01T12:00:00Z",
        "normalized_data": {
            "kind": "Pod",
            "name": "web-app-5d6f8c4b9-abcde",
            "namespace": "production",
            "status": "Running",
            "action": "running"
        },
        "deployment_history": [
            {
                "id": 1,
                "deployment_id": "abc123",
                "service_name": "web-app",
                "environment": "production",
                "status": "success",
                "timestamp": "2024-01-01T11:30:00Z"
            }
        ],
        "ownership": {
            "service": "web-app",
            "ownership": "platform-team"
        },
        "historical_patterns": {
            "total_similar_events": 5,
            "frequency_per_week": 0.8,
            "average_interval_hours": 21.5
        }
    }
    
    print("Testing summary generation...")
    summary = explainer.generate_summary(test_event)
    print(summary)
    print("\n" + "="*50 + "\n")
    
    print("Testing question answering...")
    question = "Why was the web-app pod restarted?"
    answer = explainer.answer_question(question, [test_event])
    print(f"Q: {question}")
    print(f"A: {answer}")