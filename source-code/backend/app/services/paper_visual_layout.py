"""Conservative label expansion for candidate visuals, never automatic approval."""
import re
import pymupdf

PROPOSAL_VERSION = 'visual-layout-v2'


def include_nearby_labels(page: pymupdf.Page, visual: pymupdf.Rect) -> pymupdf.Rect:
    """Find compact external labels against the original box, without chaining into neighbours.

    Labels often live in separate native PDF text blocks. This is a proposal
    heuristic: full-page crop review remains necessary for complex layouts/scans.
    """
    original=pymupdf.Rect(visual)
    expanded=pymupdf.Rect(visual)
    for block in page.get_text('dict').get('blocks',[]):
        if block.get('type') != 0:
            continue
        for line in block.get('lines',[]):
            spans=line.get('spans',[])
            text=''.join(s.get('text','') for s in spans).strip()
            box=pymupdf.Rect(line['bbox'])
            if (not text or len(text)>100 or len(text.split())>9 or box.height>35
                    or any(s.get('size',0)>16 for s in spans)
                    or re.search(r'(?:DO\s+NOT\s+WRITE|Turn over|Total for Question|P\d{6,}|\.{4,})',text,re.I)
                    or re.match(r'^\(?\s*(?:[a-z]|[ivx]+)\s*\)[\s.]',text,re.I)
                    or re.fullmatch(r'\(\d+\)',text)
                    or text.endswith(('.', '?'))
                    or re.match(r'^(?:the |this |explain |draw |calculate |state |give |name |describe |refer |use |complete |show )',text,re.I)):
                continue
            if box.x0 < page.rect.width*.07 or box.x1 > page.rect.width*.93:
                continue
            # Above/below labels must overlap the original figure horizontally;
            # side labels must overlap it vertically. Never use the expanded
            # box as the next anchor, which could swallow an adjacent caption.
            horizontal=max(0,min(box.x1,original.x1)-max(box.x0,original.x0))
            vertical=max(0,min(box.y1,original.y1)-max(box.y0,original.y0))
            xgap=max(original.x0-box.x1,box.x0-original.x1,0)
            ygap=max(original.y0-box.y1,box.y0-original.y1,0)
            aligned_vertical=horizontal>=min(box.width,original.width)*.4 and ygap<=32
            aligned_side=vertical>=min(box.height,original.height)*.5 and xgap<=85
            if aligned_vertical or aligned_side:
                expanded |= box
    return expanded & page.rect
