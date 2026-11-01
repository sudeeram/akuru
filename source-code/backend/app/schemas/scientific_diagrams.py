"""Small, typed science templates. No executable drawing instructions or remote media."""
from typing import Annotated, Literal
from pydantic import Field, model_validator
from app.schemas.worked_answers_base import StrictModel

class VolumeTimeFacts(StrictModel):
    kind: Literal['volume_time']
    xLabel: str = Field(min_length=1, max_length=80)
    yLabel: str = Field(min_length=1, max_length=80)

class EnergyFacts(StrictModel):
    kind: Literal['exothermic_profile']
    reactants: str = Field(min_length=1, max_length=100)
    products: str = Field(min_length=1, max_length=100)

class Ion(StrictModel):
    symbol: str = Field(pattern=r'^[A-Z][a-z]?$')
    atomicNumber: int = Field(ge=1, le=20)
    charge: int = Field(ge=-3, le=3)
    @model_validator(mode='after')
    def electrons(self):
        symbols=['H','He','Li','Be','B','C','N','O','F','Ne','Na','Mg','Al','Si','P','S','Cl','Ar','K','Ca']
        if self.symbol != symbols[self.atomicNumber-1] or self.charge == 0 or not 1 <= self.atomicNumber-self.charge <= 18:
            raise ValueError('Use a matching main-group element and nonzero ion charge with 1–18 electrons.')
        return self
    def shells(self):
        remaining=self.atomicNumber-self.charge
        result=[]
        for capacity in (2,8,8):
            if remaining: result.append(min(remaining,capacity));remaining-=result[-1]
        return result

class IonFacts(StrictModel):
    kind: Literal['ionic_pair']
    ions: list[Ion] = Field(min_length=2,max_length=2)
    @model_validator(mode='after')
    def opposite_charges(self):
        if not self.ions[0].charge > 0 > self.ions[1].charge:
            raise ValueError('Show a cation followed by an anion.')
        return self

DiagramFacts = Annotated[VolumeTimeFacts | EnergyFacts | IonFacts, Field(discriminator='kind')]

class DiagramInput(StrictModel):
    schemaVersion: Literal['science-diagram-v1']
    facts: DiagramFacts
    partLabels: list[str] = Field(min_length=1,max_length=12)
    verificationNote: str = Field(min_length=20,max_length=2000)
    @model_validator(mode='after')
    def distinct_parts(self):
        if len(set(self.partLabels)) != len(self.partLabels) or any(not p.strip() or len(p)>40 for p in self.partLabels):
            raise ValueError('Choose distinct valid subpart labels.')
        return self

class DiagramStep(StrictModel):
    partLabel: str = Field(min_length=1,max_length=40)
    explanation: str = Field(min_length=20,max_length=6000)

class DiagramSolution(StrictModel):
    schemaVersion: Literal['science-diagram-v1']
    title: str = Field(min_length=1,max_length=160)
    facts: DiagramFacts
    steps: list[DiagramStep] = Field(min_length=1,max_length=12)
    limitations: str = Field(min_length=1,max_length=2000)
    confidencePercent: int = Field(ge=0,le=100)
    confidenceBasis: str = Field(min_length=20,max_length=1000)
    @model_validator(mode='after')
    def distinct_steps(self):
        if len({s.partLabel for s in self.steps}) != len(self.steps):
            raise ValueError('Each step must refer to a distinct subpart.')
        return self
