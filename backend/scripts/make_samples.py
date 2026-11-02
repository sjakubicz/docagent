import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

DISCLAIMER = "Synthetic document generated for software testing. Not real patient data."

DOCS: dict[str, list[tuple[str, list[str]]]] = {
    "discharge_summary_pneumonia.pdf": [
        (
            "Discharge Summary - Community-Acquired Pneumonia",
            [
                "Patient: John Doe (fictional), 67 years old. Admitted 3 March, discharged "
                "8 March. Admitting diagnosis: right lower lobe community-acquired pneumonia "
                "confirmed by chest X-ray. CURB-65 score on admission was 2.",
                "Hospital course: the patient received intravenous ceftriaxone 1 g daily and "
                "oral azithromycin 500 mg daily for three days. Fever resolved on day 3. "
                "Oxygen saturation improved from 89% on room air to 96%.",
            ],
        ),
        (
            "Discharge Medications and Follow-up",
            [
                "Discharge medication: amoxicillin-clavulanate 875/125 mg twice daily for "
                "5 more days to complete a 7-day antibiotic course.",
                "Follow-up: primary care visit in 7 days. Repeat chest X-ray in 6 weeks to "
                "confirm resolution. Return immediately if shortness of breath worsens or "
                "fever above 38.5 C returns.",
            ],
        ),
    ],
    "metformin_medication_guide.pdf": [
        (
            "Medication Guide - Metformin",
            [
                "Metformin is a first-line medicine for type 2 diabetes. It lowers glucose "
                "production in the liver and improves insulin sensitivity.",
                "Usual starting dose: 500 mg once daily with the evening meal, increased by "
                "500 mg every week as tolerated. Maximum dose: 2000 mg per day.",
                "Common side effects are nausea, diarrhoea and abdominal discomfort; taking "
                "the tablet with food reduces them. Long-term use can lower vitamin B12 levels.",
                "Do not use metformin if eGFR is below 30 mL/min/1.73m2. Stop it temporarily "
                "before iodinated contrast imaging because of the risk of lactic acidosis.",
            ],
        )
    ],
    "lipid_panel_lab_report.pdf": [
        (
            "Laboratory Report - Fasting Lipid Panel",
            [
                "Patient: Jane Roe (fictional), 54 years old. Sample collected after a "
                "12-hour fast.",
                "Total cholesterol: 241 mg/dL (desirable below 200). LDL cholesterol: "
                "162 mg/dL (optimal below 100). HDL cholesterol: 38 mg/dL (low, desirable "
                "above 40). Triglycerides: 205 mg/dL (borderline high, normal below 150).",
                "Interpretation: elevated LDL and triglycerides with low HDL. Lifestyle "
                "changes are recommended and statin therapy should be discussed with the "
                "physician. Repeat the lipid panel in 3 months.",
            ],
        )
    ],
    "hypertension_care_plan.pdf": [
        (
            "Hypertension Care Plan",
            [
                "Diagnosis: stage 2 essential hypertension, average home blood pressure "
                "152/96 mmHg. Target blood pressure: below 130/80 mmHg.",
                "Medication: lisinopril 10 mg once daily in the morning. Check potassium "
                "and creatinine 2 weeks after starting. A dry cough is a known side effect; "
                "report it rather than stopping the drug.",
            ],
        ),
        (
            "Lifestyle and Monitoring",
            [
                "Limit sodium to less than 2 grams per day. Aim for 150 minutes of moderate "
                "exercise per week. Limit alcohol to one drink per day.",
                "Measure blood pressure at home twice daily for 7 days before each visit and "
                "bring the log. Seek emergency care for a reading above 180/120 mmHg with "
                "chest pain, headache or vision changes.",
            ],
        ),
    ],
    "asthma_action_plan.pdf": [
        (
            "Asthma Action Plan",
            [
                "Green zone (doing well): no cough or wheeze, peak flow above 80% of personal "
                "best (personal best 450 L/min). Take budesonide-formoterol 160/4.5 one "
                "inhalation twice daily.",
                "Yellow zone (getting worse): cough, wheeze or night waking, peak flow 50-80% "
                "of personal best. Take an extra inhalation of budesonide-formoterol as "
                "needed, up to 12 inhalations per day, and call the clinic within 24 hours.",
                "Red zone (medical alert): very short of breath, peak flow below 50% of "
                "personal best. Take reliever medicine and call emergency services.",
            ],
        )
    ],
}

SCANNED_DOC = (
    "knee_surgery_instructions_scan.pdf",
    "Post-operative Instructions - Arthroscopic Knee Surgery",
    [
        "Keep the dressing clean and dry for 48 hours. You may shower after 2 days.",
        "Apply ice for 20 minutes every 2 hours during the first 3 days.",
        "Use crutches and put only partial weight on the leg for 1 week.",
        "Pain relief: paracetamol 1 g every 6 hours, maximum 4 g per day.",
        "Stitches are removed at the clinic 10 to 14 days after surgery.",
        "Call the surgeon for fever above 38 C, calf pain or increasing redness.",
    ],
)


def write_text_pdf(path: Path, pages: list[tuple[str, list[str]]]) -> None:
    styles = getSampleStyleSheet()
    story = []
    for i, (title, paragraphs) in enumerate(pages):
        if i:
            story.append(PageBreak())
        story += [Paragraph(title, styles["Heading1"]), Spacer(1, 12)]
        for para in paragraphs:
            story += [Paragraph(para, styles["BodyText"]), Spacer(1, 8)]
        story.append(Paragraph(DISCLAIMER, styles["Italic"]))
    SimpleDocTemplate(str(path), pagesize=A4).build(story)


def write_scanned_pdf(path: Path, title: str, lines: list[str]) -> None:
    width, height = 1654, 2339
    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=36)
    y = 150
    draw.text((120, y), title, fill=0, font=ImageFont.load_default(size=48))
    y += 120
    for line in [*lines, "", DISCLAIMER]:
        for wrapped in textwrap.wrap(line, 70) or [""]:
            draw.text((120, y), wrapped, fill=0, font=font)
            y += 56
        y += 20
    img.save(path, "PDF", resolution=200)


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, pages in DOCS.items():
        write_text_pdf(out_dir / name, pages)
    name, title, lines = SCANNED_DOC
    write_scanned_pdf(out_dir / name, title, lines)
    print(f"Wrote {len(DOCS) + 1} PDFs to {out_dir}")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "../data/samples"))
