"""Generated solutions must preserve verified source values and safe geometry."""
import copy
import pytest
import pymupdf
from pydantic import ValidationError
from app.schemas.worked_answers import GraphSolution
from app.services.worked_answers.graphs import render, validate_source, fit_coefficients


def fixture():
    return dict(title="Synthetic heating experiment",xAxis=dict(label="Volume / cm³",minimum=0,maximum=40,tick=10),
        yAxis=dict(label="Temperature / °C",minimum=20,maximum=30,tick=2),
        points=[dict(x=x,y=y) for x,y in [(0,21),(5,22.3),(10,23.8),(15,24.4),(20,26.5),(25,28),(30,28.5),(35,28.2),(40,27.9)]],
        steps=[dict(partLabel="c(i)",explanation="Plot the verified values using crosses on the grid."),
               dict(partLabel="c(ii)",explanation="Circle the point below the initial rising trend.",circleIndexes=[3]),
               dict(partLabel="c(iii)",explanation="Fit the rising and falling sections, excluding the anomaly.",circleIndexes=[3],fits=[
                   dict(pointIndexes=[0,1,2,4,5],fromX=0,toX=32,label="Rising section"),
                   dict(pointIndexes=[6,7,8],fromX=24,toX=40,label="Falling section")])],
        limitations="Illustrative least-squares fit; valid hand-drawn fits can differ.")


def test_source_and_plot_are_valid_and_rendered_as_png():
    raw=fixture(); solution=GraphSolution.model_validate(raw)
    source={k:solution.model_dump()[k] for k in ('xAxis','yAxis','points')}
    source['partLabels']=[s.partLabel for s in solution.steps]
    validate_source(solution,source)
    for index in range(3):
        image=render(solution,index)
        assert image.startswith(b'\x89PNG')
        pix=pymupdf.Pixmap(image)
        assert pix.width==1200 and pix.height==960
    changed=copy.deepcopy(source);changed['points'][0]['y']=22
    with pytest.raises(ValueError,match='points'):validate_source(solution,changed)


@pytest.mark.parametrize('change', ['nan','outside','duplicate','anomaly','index','range','vertical'])
def test_invalid_geometry_is_rejected(change):
    raw=fixture()
    if change=='nan': raw['points'][0]['x']=float('nan')
    if change=='outside': raw['points'][0]['y']=300
    if change=='duplicate':raw['steps'][2]['fits'][0]['pointIndexes']=[0,0]
    if change=='anomaly':raw['steps'][2]['fits'][0]['pointIndexes']=[0,3]
    if change=='index':raw['steps'][1]['circleIndexes']=[100]
    if change=='range':raw['xAxis']['tick']=.0001
    if change=='vertical':raw['points'][1]['x']=0;raw['steps'][2]['fits'][0]['pointIndexes']=[0,1]
    with pytest.raises(ValidationError):GraphSolution.model_validate(raw)


def test_line_fit_is_deterministic_not_an_invented_official_reading():
    s=GraphSolution.model_validate(fixture())
    a,b=fit_coefficients([s.points[i] for i in [0,1,2,4,5]])
    c,d=fit_coefficients(s.points[6:])
    intersection=(d-b)/(a-c)
    assert 27 < intersection < 29
    assert 28 < a*intersection+b < 30
