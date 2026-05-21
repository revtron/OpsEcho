from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from datetime import datetime

Base = declarative_base()

class InfrastructureEvent(Base):
    __tablename__ = "infrastructure_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True)  # kubernetes, terraform, ci_cd, docker, aws, git
    source = Column(String)  # e.g., cluster name, repo name, etc.
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    raw_data = Column(JSON)  # Store the raw event data
    normalized_data = Column(JSON)  # After normalization
    is_processed = Column(Boolean, default=False)

    # Relationships
    summaries = relationship("EventSummary", back_populates="event", uselist=False)
    deployments = relationship("Deployment", back_populates="event")

class EventSummary(Base):
    __tablename__ = "event_summaries"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("infrastructure_events.id"))
    summary_text = Column(Text)
    operational_context = Column(JSON)  # Enriched context from the context engine
    embedding = Column(Vector(768))  # Dimension for Mistral 7B embeddings (adjust if needed)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    event = relationship("InfrastructureEvent", back_populates="summaries")

class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("infrastructure_events.id"))
    deployment_id = Column(String, unique=True, index=True)  # e.g., git commit SHA, pipeline run ID
    service_name = Column(String)
    environment = Column(String)
    status = Column(String)  # success, failure, rolled_back
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)

    # Relationship
    event = relationship("InfrastructureEvent", back_populates="deployments")

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    ownership = Column(String)  # team or owner
    dependencies = Column(JSON)  # list of service names
    metadata = Column(JSON)