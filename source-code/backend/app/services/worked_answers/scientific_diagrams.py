"""Trusted qualitative science diagrams rendered to inert PNGs from typed facts."""
import math
from html import escape
import pymupdf
from app.schemas.scientific_diagrams import DiagramSolution

RENDERER_VERSION='science-diagram-renderer-v1'

def describe_facts(facts):
    if facts.kind=='volume_time':
        return f'{facts.yLabel} against {facts.xLabel}: smooth curve from zero, rising to a horizontal plateau; no numerical data supplied.'
    if facts.kind=='exothermic_profile':
        return f'Reactants: {facts.reactants}. Products: {facts.products}. Products have lower energy. Activation energy points upwards from reactants to peak; delta H points downwards from reactants to products.'
    return '; '.join(f'{ion.symbol}: charge {ion.charge:+d}, electron arrangement '+','.join(map(str,ion.shells())) for ion in facts.ions)


def render(solution: DiagramSolution, index: int) -> bytes:
    step=solution.steps[index]
    with pymupdf.open() as pdf:
        page=pdf.new_page(width=800,height=640)
        def text(rect,value,size=14):
            page.insert_htmlbox(rect,'<div>'+escape(value)+'</div>',css=f'* {{font-family: sans-serif; font-size:{size}px;}}')
        def line(a,b,width=1.5,color=(.12,.18,.28)):
            page.draw_line(a,b,color=color,width=width)
        def arrow(a,b):
            line(a,b,2)
            angle=math.atan2(b[1]-a[1],b[0]-a[0])
            for delta in (-.45,.45):line(b,(b[0]-11*math.cos(angle+delta),b[1]-11*math.sin(angle+delta)),2)
        text((35,16,765,55),solution.title,18)
        text((35,56,765,83),f'Part {step.partLabel} · illustrative worked solution',12)
        facts=solution.facts
        if facts.kind=='volume_time':
            arrow((110,480),(710,480));arrow((110,480),(110,110))
            text((55,270,108,315),facts.yLabel,14);text((360,495,540,530),facts.xLabel)
            text((88,481,108,507),'0',12)
            shape=page.new_shape();shape.draw_bezier((110,480),(160,180),(330,180),(555,180));shape.finish(color=(.05,.35,.6),width=2.5,closePath=False);shape.commit()
            line((555,180),(690,180),2.5,(.05,.35,.6))
            text((440,135,710,175),'Reaction finished: constant volume',12)
            text((110,545,720,575),'Qualitative sketch — no numerical time or volume data supplied.',11)
        elif facts.kind=='exothermic_profile':
            arrow((95,490),(725,490));arrow((95,490),(95,110))
            text((25,200,92,245),'Energy');text((320,502,700,532),'Progress of reaction (illustrative)',12)
            line((120,320),(215,320),2.5,(.05,.35,.6))
            shape=page.new_shape();shape.draw_bezier((215,320),(265,320),(320,120),(395,120));shape.draw_bezier((395,120),(470,120),(500,430),(580,430));shape.finish(color=(.05,.35,.6),width=2.5,closePath=False);shape.commit()
            line((580,430),(700,430),2.5,(.05,.35,.6))
            line((215,320),(650,320),.6,(.65,.68,.72));line((288,120),(395,120),.6,(.65,.68,.72))
            arrow((288,320),(288,120));arrow((640,320),(640,430))
            text((120,330,275,390),'Reactants: '+facts.reactants,12)
            text((520,440,720,480),'Products: '+facts.products,12)
            text((140,180,280,250),'Activation energy, Eₐ',13)
            text((650,354,760,392),'ΔH < 0',15)
            text((110,547,735,576),'Arrows: Eₐ upwards to the peak; ΔH downwards to the product level.',11)
        else:
            for cx,ion in zip((225,580),facts.ions):
                shells=ion.shells()
                for shell,count in enumerate(shells):
                    radius=45+40*shell
                    page.draw_circle((cx,290),radius,color=(.4,.47,.56),width=1)
                    for i in range(count):
                        angle=-math.pi/2+2*math.pi*i/count
                        page.draw_circle((cx+radius*math.cos(angle),290+radius*math.sin(angle)),3,color=(.05,.25,.5),fill=(.05,.25,.5))
                text((cx-25,275,cx+35,310),ion.symbol,18)
                for side in (-1,1):
                    x=cx+side*145
                    line((x-side*15,140),(x,140));line((x,140),(x,440));line((x,440),(x-side*15,440))
                magnitude=abs(ion.charge);charge=('' if magnitude==1 else str(magnitude))+('+' if ion.charge>0 else '−')
                text((cx+148,122,cx+185,156),charge,19)
                text((cx-120,470,cx+135,505),'Electron arrangement: '+','.join(map(str,shells)),13)
            text((110,545,740,577),'Each ion has ten electrons for Mg²⁺ and O²⁻; dots represent electrons.' if [i.symbol for i in facts.ions]==['Mg','O'] and [i.charge for i in facts.ions]==[2,-2] else 'Dots represent electrons. Brackets and ion charges are shown.',12)
        text((35,590,775,630),'AI-generated worked answer — not an official Pearson answer',12)
        return page.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False).tobytes('png')
