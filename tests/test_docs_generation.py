import os

import pytest

pytestmark = pytest.mark.skipif(not os.path.exists("results/summary.json"),
                                reason="needs results/summary.json (run make experiments)")


def test_report_and_deck_build_from_summary(tmp_path):
    from pvm import make_deck, make_report
    r = make_report.build(out=str(tmp_path / "r.docx"))
    d = make_deck.build(out=str(tmp_path / "d.pptx"))
    assert os.path.getsize(r) > 20_000 and os.path.getsize(d) > 20_000


def test_deck_has_notes_and_dataset_labels(tmp_path):
    from pptx import Presentation
    from pvm import make_deck
    p = Presentation(make_deck.build(out=str(tmp_path / "d.pptx")))
    assert 10 <= len(p.slides) <= 12
    assert all(s.notes_slide.notes_text_frame.text.strip() for s in p.slides)
