"""Bounded declarative graph specifications; never executable model code."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Axis(StrictModel):
    label: str = Field(min_length=1, max_length=120)
    minimum: float = Field(ge=-1e9, le=1e9)
    maximum: float = Field(ge=-1e9, le=1e9)
    tick: float = Field(gt=0)

    @model_validator(mode="after")
    def bounds(self):
        if self.maximum <= self.minimum or not 1 <= (self.maximum-self.minimum)/self.tick <= 40:
            raise ValueError("Axis needs an increasing range and between 1 and 40 tick intervals.")
        return self


class Point(StrictModel):
    x: float = Field(ge=-1e9, le=1e9)
    y: float = Field(ge=-1e9, le=1e9)


class Fit(StrictModel):
    pointIndexes: list[int] = Field(min_length=2, max_length=100)
    fromX: float
    toX: float
    label: str = Field(min_length=1, max_length=100)


class WorkedStep(StrictModel):
    partLabel: str = Field(min_length=1, max_length=40)
    explanation: str = Field(min_length=20, max_length=6000)
    showPoints: Literal[True] = True
    circleIndexes: list[int] = Field(default_factory=list, max_length=100)
    fits: list[Fit] = Field(default_factory=list, max_length=6)


class GraphSolution(StrictModel):
    schemaVersion: Literal["graph-v1"] = "graph-v1"
    title: str = Field(min_length=1, max_length=160)
    xAxis: Axis
    yAxis: Axis
    points: list[Point] = Field(min_length=2, max_length=100)
    steps: list[WorkedStep] = Field(min_length=1, max_length=12)
    limitations: str = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def validate_geometry(self):
        if len({s.partLabel for s in self.steps}) != len(self.steps):
            raise ValueError("Each step must refer to a distinct subpart.")
        for p in self.points:
            if not self.xAxis.minimum <= p.x <= self.xAxis.maximum or not self.yAxis.minimum <= p.y <= self.yAxis.maximum:
                raise ValueError("A plotted point falls outside the reviewed axes.")
        for step in self.steps:
            if len(set(step.circleIndexes)) != len(step.circleIndexes):
                raise ValueError("Duplicate anomaly index.")
            for i in step.circleIndexes:
                if not 0 <= i < len(self.points):
                    raise ValueError("Invalid anomaly index.")
            for fit in step.fits:
                if len(set(fit.pointIndexes)) != len(fit.pointIndexes):
                    raise ValueError("Duplicate fitting point.")
                if any(not 0 <= i < len(self.points) for i in fit.pointIndexes):
                    raise ValueError("Invalid fitting point.")
                if set(fit.pointIndexes) & set(step.circleIndexes):
                    raise ValueError("An anomalous point cannot be included in a best-fit line.")
                if len({self.points[i].x for i in fit.pointIndexes}) < 2:
                    raise ValueError("A best-fit line needs distinct x coordinates.")
                if not self.xAxis.minimum <= fit.fromX < fit.toX <= self.xAxis.maximum:
                    raise ValueError("Invalid fitting line extent.")
        return self


class GraphInput(StrictModel):
    xAxis: Axis
    yAxis: Axis
    points: list[Point] = Field(min_length=2, max_length=100)
    partLabels: list[str] = Field(min_length=1, max_length=12)
    verificationNote: str = Field(min_length=20, max_length=2000)

    @model_validator(mode="after")
    def source_geometry(self):
        if len(set(self.partLabels)) != len(self.partLabels) or any(not p.strip() or len(p)>40 for p in self.partLabels):
            raise ValueError("Choose distinct valid subpart labels.")
        for p in self.points:
            if not self.xAxis.minimum <= p.x <= self.xAxis.maximum or not self.yAxis.minimum <= p.y <= self.yAxis.maximum:
                raise ValueError("Source point is outside the axis range.")
        return self


class GenerateWorkedAnswer(StrictModel):
    expectedQuestionRevision: int = Field(ge=1)
    graph: GraphInput
    regenerate: bool = False


class ReviewWorkedAnswer(StrictModel):
    expectedRevision: int = Field(ge=1)
    action: Literal["edit", "approve", "reject"]
    solution: GraphSolution | None = None
    reviewNote: str = Field(min_length=20, max_length=2000)


class AttachWorkedAnswer(StrictModel):
    expectedQuestionRevision: int = Field(ge=1)
