"""Trusted renderer helpers for fixed scientific semantics and verified plot data."""
from html import escape

def describe(f):
    if f.kind=='pyramid_of_numbers':
        return 'Pyramid of numbers, bottom to top: '+ '; '.join(f'{p.label}: {p.count}'for p in f.levels)+'. Centred bars have equal heights; widths are proportional to counts on one linear scale, not biomass or organism size.'
    if f.kind=='monohybrid_cross':
        d=f.dominant_count();text=f'Parents {f.parents[0]} × {f.parents[1]}; gametes from each parent are its individual alleles. Offspring '+', '.join(f.outcomes())+f'. Phenotype ratio {d} {f.dominantPhenotype} : {4-d} {f.recessivePhenotype}.'
        if f.target!='phenotype_ratio':text+=f' P({f.target.replace("_"," and ")}) = {f.probability()}; sex and trait are assumed independent when combined.'
        return text
    if f.kind=='paired_line_graph':
        return f'{f.xAxis.label} against {f.yAxis.label}. '+ '; '.join(f'{p.x:g}: {f.labelA} {p.yA:g}, {f.labelB} {p.yB:g}'for p in f.points)+'. Join consecutive observations separately for each series with straight segments; no fitted trend or invented observations.'
    return 'Left/outside the jar: iodine turns blue-black, indicating starch. Right/inside the carbon-dioxide-absorbing jar: iodine remains yellow/orange/brown, indicating no starch. Labels and colours must agree.'

def render(page,f,text,line,arrow):
    if f.kind=='pyramid_of_numbers':
        largest=max(p.count for p in f.levels)
        height=min(80,300/len(f.levels))
        for i,p in enumerate(f.levels):
            half=220*p.count/largest
            bottom=460-i*height
            page.draw_rect((330-half,bottom-height,330+half,bottom),color=(.1,.3,.5),fill=(.72,.85,.92))
            text((575,bottom-height+12,770,bottom-2),f'{p.label}: {p.count}',15)
            line((330+half,bottom-height/2),(565,bottom-height/2),.8)
        text((65,108,755,147),'Pyramid of numbers — producer at the bottom',16)
        text((65,490,755,535),'Equal bar heights; widths proportional to the source counts on a single linear scale.',13)
        text((65,543,755,577),'Numbers of organisms, not their mass or physical size.',12)
    elif f.kind=='monohybrid_cross':
        text((65,95,750,130),f'Parents: {f.parents[0]} × {f.parents[1]}',18)
        text((65,135,750,170),'Gametes: '+ ' or '.join(dict.fromkeys(f.parents[0]))+'  ×  '+' or '.join(dict.fromkeys(f.parents[1])),16)
        xs=[220,330,500,670];ys=[190,245,325,405];out=f.outcomes()
        cells=[['Gametes',*f.parents[1]],[f.parents[0][0],out[0],out[1]],[f.parents[0][1],out[2],out[3]]]
        for x in xs:line((x,ys[0]),(x,ys[-1]))
        for y in ys:line((xs[0],y),(xs[-1],y))
        for r,row in enumerate(cells):
            for c,v in enumerate(row):text((xs[c]+12,ys[r]+12,xs[c+1]-5,ys[r+1]-5),v,18)
        d=f.dominant_count();text((65,430,750,470),f'Phenotype ratio: {d} {f.dominantPhenotype} : {4-d} {f.recessivePhenotype}',17)
        if f.target!='phenotype_ratio':
            p=f.probability();text((65,480,750,520),f'P({f.target.replace("_"," and ")}) = {p} = {float(p)*100:g}%',17)
            text((65,538,750,575),'Combined sex/trait calculation assumes independent inheritance.',12)
        else:text((65,510,750,560),'Ratios are probabilities, not guaranteed numbers in a small family.',12)
    elif f.kind=='paired_line_graph':
        left,right,top,bottom=115,720,145,480
        def px(v):return left+(v-f.xAxis.minimum)/(f.xAxis.maximum-f.xAxis.minimum)*(right-left)
        def py(v):return bottom-(v-f.yAxis.minimum)/(f.yAxis.maximum-f.yAxis.minimum)*(bottom-top)
        import math
        for axis,horiz in [(f.xAxis,True),(f.yAxis,False)]:
            for i in range(math.floor((axis.maximum-axis.minimum)/axis.tick+1e-9)+1):
                v=axis.minimum+i*axis.tick
                if horiz:
                    x=px(v);line((x,top),(x,bottom),.5,(.82,.85,.88));text((x-15,bottom+4,x+25,bottom+26),f'{v:g}',11)
                else:
                    y=py(v);line((left,y),(right,y),.5,(.82,.85,.88));text((left-55,y-9,left-4,y+15),f'{v:g}',11)
        line((left,top),(left,bottom));line((left,bottom),(right,bottom))
        page.insert_htmlbox((15,180,45,470),'<div>'+escape(f.yAxis.label)+'</div>',css='* {font-family: sans-serif; font-size:13px;}',rotate=90)
        text((270,516,725,548),f.xAxis.label,13)
        for field,label,color,ly in [('yA',f.labelA,(.05,.3,.65),92),('yB',f.labelB,(.65,.15,.1),115)]:
            line((440,ly+7),(480,ly+7),2,color);text((490,ly-7,740,ly+18),label,13)
            previous=None
            for p in f.points:
                x,y=px(p.x),py(getattr(p,field))
                if previous:line(previous,(x,y),2,color)
                page.draw_circle((x,y),2.7,color=color,fill=color);previous=(x,y)
        text((115,554,750,579),'Straight joins connect verified source observations; no extrapolation.',11)
    else:
        # Two labelled regions; colour is not the sole carrier of meaning.
        page.draw_rect((110,245,400,375),color=(.1,.15,.2),fill=(.06,.08,.2))
        page.draw_rect((400,245,690,375),color=(.1,.15,.2),fill=(.72,.45,.15))
        text((85,125,380,190),'LEFT: outside jar, carbon dioxide available',17)
        text((430,125,740,190),'RIGHT: inside jar, carbon dioxide absorbed',17)
        arrow((245,200),(245,240));arrow((550,200),(550,240))
        text((85,407,390,475),'Blue-black: starch present',18)
        text((420,407,750,480),'Yellow/orange/brown: no starch',18)
        text((90,522,745,567),'Schematic iodine-test result: labels and colours must agree.',12)
