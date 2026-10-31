import pymupdf
from app.services.paper_visual_layout import include_nearby_labels


def test_captions_below_separate_structures_are_preserved_without_chaining():
    with pymupdf.open() as pdf:
        page=pdf.new_page(width=600,height=800)
        page.insert_text((170,210),'Structure A',fontsize=11)
        page.insert_text((330,210),'Structure B',fontsize=11)
        original=pymupdf.Rect(160,110,245,180)
        expanded=include_nearby_labels(page,original)
        assert expanded.y1>210
        assert expanded.x1<300
        assert expanded.contains(original)


def test_external_apparatus_labels_and_axis_titles_are_included_but_not_question_text():
    with pymupdf.open() as pdf:
        page=pdf.new_page(width=600,height=800)
        page.insert_text((130,220),'Volume',fontsize=11)
        page.insert_text((280,330),'Time',fontsize=11)
        page.insert_text((75,100),'(c) Draw a graph to show the results.',fontsize=11)
        page.insert_text((75,380),'DO NOT WRITE IN THIS AREA',fontsize=11)
        original=pymupdf.Rect(200,140,420,310)
        expanded=include_nearby_labels(page,original)
        assert expanded.x0<=130 and expanded.y1>=330
        assert expanded.y0==140 and expanded.y1<380


def test_intentionally_blank_axes_are_not_labelled_from_other_sources():
    with pymupdf.open() as pdf:
        page=pdf.new_page(width=600,height=800)
        original=pymupdf.Rect(170,180,430,400)
        assert include_nearby_labels(page,original)==original
