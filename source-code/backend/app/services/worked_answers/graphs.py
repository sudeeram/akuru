"""Trusted graph rendering from a validated specification, with no generated code."""
import math
import pymupdf
from app.schemas.worked_answers import GraphSolution

LABEL = "AI-generated worked answer — not an official Pearson answer"
RENDERER_VERSION = "graph-renderer-v1"


def fit_coefficients(points):
    """Ordinary least squares is an illustrative fit, not an official tolerance."""
    mx = sum(p.x for p in points)/len(points)
    my = sum(p.y for p in points)/len(points)
    slope = sum((p.x-mx)*(p.y-my) for p in points)/sum((p.x-mx)**2 for p in points)
    return slope, my-slope*mx


def validate_source(solution: GraphSolution, source: dict):
    """Source table and axes must be explicitly verified, never inferred silently."""
    for key in ("xAxis", "yAxis", "points"):
        expected = source.get(key)
        if expected != solution.model_dump()[key]:
            raise ValueError(f"Generated {key} differs from the verified graph input.")
    if set(s.partLabel for s in solution.steps) != set(source.get("partLabels", [])):
        raise ValueError("Generated steps do not match the selected subparts.")


def render(solution: GraphSolution, step_index: int) -> bytes:
    """Raster PNG keeps model-generated strings inert and preserves aspect ratio."""
    step = solution.steps[step_index]
    left, top, width, height = 105, 80, 600, 420
    x, y = solution.xAxis, solution.yAxis
    def px(v): return left+(v-x.minimum)/(x.maximum-x.minimum)*width
    def py(v): return top+height-(v-y.minimum)/(y.maximum-y.minimum)*height
    with pymupdf.open() as pdf:
        page = pdf.new_page(width=800, height=640)
        # HTML text insertion uses an escaped document for scientific Unicode.
        from html import escape
        def text(rect, value, size=11, rotation=0):
            page.insert_htmlbox(rect, '<div>'+escape(value)+'</div>', css=f'* {{font-family: sans-serif; font-size: {size}px;}}', rotate=rotation)
        text((35,15,770,55), solution.title, 16)
        text((35,55,770,77), f"Part {step.partLabel} · illustrative worked solution")
        for axis, horizontal in ((x,True),(y,False)):
            count=math.floor((axis.maximum-axis.minimum)/axis.tick+1e-9)
            for i in range(count+1):
                v=axis.minimum+i*axis.tick
                if horizontal:
                    p=px(v); page.draw_line((p,top),(p,top+height),color=(.8,.83,.87),width=.5)
                    text((p-22,top+height+5,p+30,top+height+25),f'{v:g}')
                else:
                    p=py(v); page.draw_line((left,p),(left+width,p),color=(.8,.83,.87),width=.5)
                    text((left-52,p-9,left-3,p+15),f'{v:g}')
        page.draw_rect((left,top,left+width,top+height),color=(.1,.15,.2),width=1)
        text((left,top+height+33,left+width,top+height+60),x.label,13)
        text((10,top+30,35,top+height-30),y.label,13,rotation=90)
        if step.showPoints:
            for p in solution.points:
                a,b=px(p.x),py(p.y)
                page.draw_line((a-3,b-3),(a+3,b+3),color=(.05,.25,.6),width=1.2)
                page.draw_line((a-3,b+3),(a+3,b-3),color=(.05,.25,.6),width=1.2)
        for index in step.circleIndexes:
            p=solution.points[index]
            page.draw_circle((px(p.x),py(p.y)),9,color=(.7,.2,.05),width=1.4)
        for fit in step.fits:
            slope,intercept=fit_coefficients([solution.points[i] for i in fit.pointIndexes])
            lo,hi=fit.fromX,fit.toX
            if slope:
                a,b=sorted(((y.minimum-intercept)/slope,(y.maximum-intercept)/slope))
                lo,hi=max(lo,a),min(hi,b)
            elif not y.minimum <= intercept <= y.maximum:
                raise ValueError("Fitted line is outside the plot.")
            if hi <= lo: raise ValueError("Fitted line has no visible extent.")
            page.draw_line((px(lo),py(slope*lo+intercept)),(px(hi),py(slope*hi+intercept)),color=(.1,.5,.3),width=1.3)
        text((35,585,770,630),LABEL,12)
        return page.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False).tobytes('png')
