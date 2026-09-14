import base64
from types import SimpleNamespace
import pytest
from app.ai.image_provider import OpenAIImageProvider
from app.errors import DomainError
from app.services.media import _svg

def test_controlled_svg_escapes_text_and_validates_geometry_and_plot():
    svg=_svg("forces_svg",{"left":8,"right":12},"Forces <script>","Two & opposite forces").decode()
    assert "&lt;script&gt;" in svg and "Two &amp; opposite" in svg and "<script>" not in svg
    assert "8 N" in svg and "12 N" in svg
    with pytest.raises(DomainError,match="less than 180"):
        _svg("geometry_svg",{"angleA":100,"angleB":90},"Triangle","A triangle with labelled angles")
    plot=_svg("plot_svg",{"points":[[0,0],[1,2],[2,4]]},"Distance graph","Distance increases with time")
    assert b"<polyline" in plot and plot.count(b"<circle") == 3

def test_openai_image_provider_decodes_private_png():
    content=b"\x89PNG\r\n\x1a\nprivate"
    images=SimpleNamespace(generate=lambda **kwargs: SimpleNamespace(id="image-response",data=[SimpleNamespace(b64_json=base64.b64encode(content).decode())]))
    provider=OpenAIImageProvider("secret","image-model","1024x1024",10,client=SimpleNamespace(images=images))
    result=provider.generate("Grounded educational diagram")
    assert result.content == content and result.content_type == "image/png" and result.response_id == "image-response"
