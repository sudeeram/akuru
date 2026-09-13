# Deterministic extraction fixtures

The automated tests generate compact PDFs from the five subject specifications in `subjects.json`. Generated files stay in pytest temporary directories so the repository does not contain Pearson material or opaque binary fixtures.

Each fixture exercises a distinct source feature: Maths equations, Science diagrams, ICT tables, English headings/paragraphs, and French OCR/language fallback. These are pipeline contract fixtures, not an accuracy benchmark. Reviewed real-document evaluation is required before publishing extracted learning content.
