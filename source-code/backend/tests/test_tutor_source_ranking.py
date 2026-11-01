from types import SimpleNamespace as Row
from app.services.tutor_sources import _rank_evidence


def record(text,kind='paragraph',asset=None,page=1):
    return (Row(content=text,page_number=page,source_ordinal=1),Row(block_kind=kind,source_asset_id=asset),.95)


def test_exact_approved_figure_wins_without_prefix_collision():
    rows=[record('Figure 1.14. A diffusion tube','diagram','asset14'),record('Figure 1.4. Particle arrangements','diagram','asset4')]
    ranked=_rank_evidence('Show Figure 1.4',rows,{'asset4','asset14'},.45)
    assert len(ranked)==1 and ranked[0][0].content.startswith('Figure 1.4.')
    assert not _rank_evidence('Show Figure 1.4',rows,set(),.45)


def test_lexical_fallback_finds_content_but_not_exercise_only_answers():
    rows=[record('Explain why ammonia diffuses faster than hydrogen chloride.','question'),
          record('Ammonia diffuses faster than hydrogen chloride because its particles are lighter.')]
    ranked=_rank_evidence('Why does ammonia diffuse faster than hydrogen chloride?',rows,set(),.45)
    assert len(ranked)==1 and 'because' in ranked[0][0].content


def test_single_incidental_term_does_not_broaden_topic_scope():
    rows=[record('Solubility describes how much solute dissolves in a solvent.'),record('Particles move randomly in gases.')]
    assert not _rank_evidence('Teach chemical equilibrium constants Kc',rows,set(),.45)
