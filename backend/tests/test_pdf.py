from docagent.ingest.pdf import extract_pages


def test_text_pdf_uses_text_layer(sample_pdf):
    pages = extract_pages(str(sample_pdf))
    assert len(pages) == 2
    assert not any(p.ocr for p in pages)
    assert "lisinopril 10 mg" in pages[0].text


def test_scanned_pdf_falls_back_to_ocr(scanned_pdf):
    (page,) = extract_pages(str(scanned_pdf))
    assert page.ocr
    assert "paracetamol" in page.text.lower()
