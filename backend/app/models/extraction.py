from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    problem = "problem"
    method = "method"
    architecture = "architecture"
    concept = "concept"
    dataset = "dataset"
    experiment = "experiment"
    result = "result"
    citation = "citation"
    limitation = "limitation"
    future_work = "future_work"
    reasoning = "reasoning"


class RelationshipType(str, Enum):
    BUILDS_ON = "BUILDS_ON"
    CITES = "CITES"
    USES_DATASET = "USES_DATASET"
    EVALUATED_ON = "EVALUATED_ON"
    COMPARES_TO = "COMPARES_TO"
    IMPROVES = "IMPROVES"
    DERIVES_FROM = "DERIVES_FROM"
    PRODUCES_RESULT = "PRODUCES_RESULT"
    EXTENDS = "EXTENDS"
    CONTRADICTS = "CONTRADICTS"
    USES = "USES"
    DEFINES = "DEFINES"
    LEADS_TO = "LEADS_TO"


class Entity(BaseModel):
    title: str = Field(description="Short descriptive title of the entity")
    type: NodeType = Field(description="Entity type")
    description: str = Field(description="Detailed explanation of this entity")
    simplified_explanation: Optional[str] = Field(
        default=None, description="Plain-language explanation for non-experts"
    )
    advantages: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    key_equations: list[str] = Field(
        default_factory=list,
        description="LaTeX strings of key equations related to this entity",
    )
    source_text: Optional[str] = Field(
        default=None, description="Verbatim excerpt from the paper"
    )
    section_name: Optional[str] = Field(
        default=None, description="Section name, e.g. '3.2 Self-Attention'"
    )
    section_number: Optional[str] = Field(
        default=None, description="Section number, e.g. '3.2'"
    )
    page_number: Optional[int] = Field(
        default=None, description="PDF page number (1-indexed)"
    )
    label: Optional[str] = Field(
        default=None,
        description="Label as it appears in the paper, e.g. 'Equation 6a', 'Figure 3'",
    )


class Relationship(BaseModel):
    source_title: str = Field(description="Title of the source entity")
    target_title: str = Field(description="Title of the target entity")
    relationship_type: RelationshipType


class SectionInfo(BaseModel):
    section_number: str
    section_name: str
    page_start: int
    page_end: Optional[int] = None


class PaperStructure(BaseModel):
    title: str
    abstract: str
    authors: list[str] = Field(default_factory=list)
    sections: list[SectionInfo] = Field(default_factory=list)


class PaperEntities(BaseModel):
    entities: list[Entity] = Field(default_factory=list)


class PaperRelationships(BaseModel):
    relationships: list[Relationship] = Field(default_factory=list)


class ReasoningStep(BaseModel):
    title: str
    description: str
    section_name: Optional[str] = None
    page_number: Optional[int] = None


class PaperReasoningFlow(BaseModel):
    steps: list[ReasoningStep] = Field(
        default_factory=list,
        description="Ordered reasoning steps: problem → prior limitations → method → experiments → results → conclusion",
    )
