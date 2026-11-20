"""Bounded, source-verified Biology diagrams; no executable drawing primitives."""
from fractions import Fraction
from typing import Literal
from pydantic import Field,model_validator
from app.schemas.worked_answers_base import StrictModel

class MonohybridFacts(StrictModel):
    kind: Literal['monohybrid_cross']
    dominantAllele: str=Field(pattern=r'^[A-Z]$')
    recessiveAllele: str=Field(pattern=r'^[a-z]$')
    parents: list[str]=Field(min_length=2,max_length=2)
    dominantPhenotype: str=Field(min_length=1,max_length=50)
    recessivePhenotype: str=Field(min_length=1,max_length=50)
    target: Literal['phenotype_ratio','dominant','recessive','male_dominant','male_recessive','female_dominant','female_recessive']
    @model_validator(mode='after')
    def alleles(self):
        if self.dominantAllele.lower()!=self.recessiveAllele:
            raise ValueError('Use a consistent uppercase/lowercase allele pair.')
        if any(len(p)!=2 or set(p)-{self.dominantAllele,self.recessiveAllele}for p in self.parents):
            raise ValueError('Each diploid parent must contain two verified alleles.')
        return self
    def outcomes(self):
        return [''.join(sorted((a,b),key=lambda c:c!=self.dominantAllele))for a in self.parents[0]for b in self.parents[1]]
    def dominant_count(self):return sum(self.dominantAllele in p for p in self.outcomes())
    def probability(self):
        count=self.dominant_count()if self.target.endswith('dominant')else 4-self.dominant_count()
        return Fraction(count,8 if self.target.startswith(('male_','female_'))else 4)

class PlotAxis(StrictModel):
    label: str=Field(min_length=1,max_length=100)
    minimum: float=Field(ge=-1e9,le=1e9)
    maximum: float=Field(ge=-1e9,le=1e9)
    tick: float=Field(gt=0)
    @model_validator(mode='after')
    def range(self):
        if self.maximum<=self.minimum or not 1<=(self.maximum-self.minimum)/self.tick<=40:raise ValueError('Choose increasing axes with 1–40 intervals.')
        return self

class PairedPoint(StrictModel):
    x: float=Field(ge=-1e9,le=1e9)
    yA: float=Field(ge=-1e9,le=1e9)
    yB: float=Field(ge=-1e9,le=1e9)

class PairedLineFacts(StrictModel):
    kind: Literal['paired_line_graph']
    xAxis: PlotAxis
    yAxis: PlotAxis
    labelA: str=Field(min_length=1,max_length=50)
    labelB: str=Field(min_length=1,max_length=50)
    points: list[PairedPoint]=Field(min_length=2,max_length=40)
    @model_validator(mode='after')
    def coordinates(self):
        if self.labelA==self.labelB:raise ValueError('Series labels must differ.')
        if any(a.x>=b.x for a,b in zip(self.points,self.points[1:])):raise ValueError('Source observations must have increasing x values.')
        if any(not self.xAxis.minimum<=p.x<=self.xAxis.maximum or not all(self.yAxis.minimum<=y<=self.yAxis.maximum for y in (p.yA,p.yB))for p in self.points):raise ValueError('Source points must lie within the verified axes.')
        return self

class StarchLeafFacts(StrictModel):
    kind: Literal['starch_leaf_halves']
    left: Literal['outside_jar_starch_present']
    right: Literal['inside_co2_absorbing_jar_starch_absent']

class NumberPyramidLevel(StrictModel):
    label: str=Field(min_length=1,max_length=60)
    count: int=Field(strict=True,ge=1,le=1000000000)

class NumberPyramidFacts(StrictModel):
    """Source counts in producer-to-top-consumer order; widths are derived."""
    kind: Literal['pyramid_of_numbers']
    levels: list[NumberPyramidLevel]=Field(min_length=2,max_length=5)
    @model_validator(mode='after')
    def distinct_labels(self):
        if len({p.label.strip().casefold()for p in self.levels})!=len(self.levels):
            raise ValueError('Use distinct trophic-level labels.')
        if any(not p.label.strip()for p in self.levels):
            raise ValueError('Use nonblank trophic-level labels.')
        if min(p.count for p in self.levels)/max(p.count for p in self.levels)<1/200:
            raise ValueError('Count ratio is too small for a legible linear-scale pyramid; choose another presentation.')
        return self
