"""Trusted qualitative science diagrams rendered to inert PNGs from typed facts."""
import math
from html import escape
import pymupdf
from app.schemas.scientific_diagrams import DiagramSolution

RENDERER_VERSION='science-diagram-renderer-v2'

def describe_facts(facts):
    if facts.kind=='volume_time':
        return f'{facts.yLabel} against {facts.xLabel}: smooth curve from zero, rising to a horizontal plateau; no numerical data supplied.'
    if facts.kind=='exothermic_profile':
        return f'Reactants: {facts.reactants}. Products: {facts.products}. Products have lower energy. Activation energy points upwards from reactants to peak; delta H points downwards from reactants to products.'
    if facts.kind=='roan_cross':
        return 'Roan parents CᵂCᴿ × CᵂCᴿ; gametes Cᵂ or Cᴿ from each. Offspring: 1 CᵂCᵂ (white), 2 CᵂCᴿ (roan), 1 CᴿCᴿ (red). P(male and roan) = 1/2 × 1/2 = 1/4 = 25%, assuming independent sex and coat-colour inheritance.'
    if facts.kind=='bubble_potometer':
        return 'Labelled leafy shoot, airtight seal, water-filled capillary tube, air bubble and scale. Bubble movement estimates water uptake per unit time, a proxy for transpiration; not a direct measurement of all water lost.'
    if facts.kind=='clotting_temperature':
        return 'Temperature (°C), 30–42, against time to clot (qualitative). Time decreases to a minimum at 37°C, then increases. No numerical clotting times supplied or invented.'
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
        elif facts.kind=='roan_cross':
            text((85,95,735,130),'Parents: roan CᵂCᴿ  ×  roan CᵂCᴿ',18)
            text((85,135,735,165),'Gametes from each parent: Cᵂ or Cᴿ',16)
            xs=[230,340,500,660]; ys=[190,245,325,405]
            for x in xs: line((x,ys[0]),(x,ys[-1]))
            for y in ys: line((xs[0],y),(xs[-1],y))
            cells=[['Gametes','Cᵂ','Cᴿ'],['Cᵂ','CᵂCᵂ (white)','CᵂCᴿ (roan)'],['Cᴿ','CᵂCᴿ (roan)','CᴿCᴿ (red)']]
            for r,row in enumerate(cells):
                for c,value in enumerate(row): text((xs[c]+8,ys[r]+14,xs[c+1]-4,ys[r+1]-3),value,15)
            text((85,433,740,470),'Roan offspring: 2 out of 4 = 1/2',17)
            text((85,477,740,517),'P(male and roan) = 1/2 × 1/2 = 1/4 = 25%',18)
            text((85,535,740,575),'Assumes independent inheritance of sex and coat colour.',12)
        elif facts.kind=='bubble_potometer':
            # Water-filled bent glass tube: connected to the sealed leafy shoot.
            blue=(.12,.4,.7)
            line((205,244),(205,391),2,blue);line((205,391),(680,391),2,blue)
            line((225,244),(225,375),2,blue);line((225,375),(680,375),2,blue)
            page.draw_rect((190,218,240,244),color=(.3,.3,.3),fill=(.8,.8,.75))
            line((215,268),(215,125),4,(.1,.4,.2))
            for x,y,dx in [(215,145,-55),(215,175,65),(215,205,-65)]:
                line((x,y),(x+dx,y-22),3,(.1,.4,.2))
                page.draw_oval((min(x+dx,x+dx*.4),y-50,max(x+dx,x+dx*.4)+20,y-12),color=(.1,.4,.2),fill=(.65,.83,.64))
            page.draw_oval((430,377,458,389),color=blue,fill=(1,1,1))
            # Unnumbered scale avoids fabricated measurements.
            line((300,415),(675,415))
            for x in range(300,676,15):line((x,415),(x,425 if x%30==0 else 421))
            text((35,92,195,130),'Leafy shoot (plant)',14);line((175,125),(185,148))
            text((270,200,650,234),'Airtight seal / petroleum jelly',14);line((280,233),(239,232))
            text((390,280,715,315),'Water-filled capillary tube',14);line((530,316),(555,375))
            text((340,330,460,360),'Air bubble',14);line((420,356),(444,378))
            text((490,445,720,478),'Scale / ruler',14);line((550,445),(550,420))
            arrow((470,355),(380,355));text((360,240,720,274),'Bubble moves towards the shoot',12)
            text((70,500,745,543),'Measure bubble displacement per unit time; water uptake is a proxy for transpiration.',14)
            text((70,549,745,578),'Schematic only: no invented readings or apparatus dimensions.',11)
        elif facts.kind=='clotting_temperature':
            left,right,base,top=135,710,470,125
            arrow((left,base),(right+15,base));arrow((left,base),(left,top))
            text((20,220,125,310),'Time to clot\n(qualitative)',14)
            text((315,515,710,552),'Temperature (°C)',16)
            def px(t):return left+(t-30)/12*(right-left)
            for t in (30,32,34,36,37,38,40,42):
                x=px(t);line((x,base),(x,base+6));text((x-13,base+10,x+20,base+35),str(t),12)
            shape=page.new_shape()
            shape.draw_bezier((px(30),175),(px(33),310),(px(35.5),410),(px(37),410))
            shape.draw_bezier((px(37),410),(px(38),410),(px(40),260),(px(42),150))
            shape.finish(color=(.05,.35,.6),width=2.5,closePath=False);shape.commit()
            text((280,105,710,141),'Shortest clotting time at 37°C',15)
            arrow((495,155),(px(37),400))
            text((95,554,740,579),'Qualitative sketch: no numerical clotting-time data supplied.',12)
        elif facts.kind=='ionic_pair':
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
