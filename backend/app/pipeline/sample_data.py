from pathlib import Path
import pymupdf
from backend.app.pipeline.registry import DocumentRegistry

def create_sample_energy_pdf(output_path: Path) -> Path:
    doc = pymupdf.open()

    # --- PAGE 1: Overview & Executive Summary ---
    page1 = doc.new_page(width=612, height=792)
    page1.insert_text((54, 60), "GLOBAL CLEAN ENERGY & INVESTMENT OUTLOOK 2024", fontsize=15)
    page1.insert_text((54, 82), "International Transition & Sustainability Review - Special Report", fontsize=10)
    page1.draw_line((54, 92), (558, 92), color=(0.2, 0.4, 0.6), width=1.5)

    page1.insert_text((54, 120), "1. EXECUTIVE SUMMARY", fontsize=12)
    summary_text = (
        "Global capital deployment into zero-carbon energy reached record levels in 2023. Total investments "
        "across generation, electrified transport, and grid infrastructure approached 985 billion USD. "
        "Solar photovoltaic technologies led additions, followed by steady expansion in onshore and offshore wind. "
        "Electric vehicle adoption expanded in key markets, while power grid resilience remains a vital bottleneck."
    )
    rect1 = pymupdf.Rect(54, 135, 558, 210)
    page1.insert_textbox(rect1, summary_text, fontsize=10, lineheight=1.4)

    page1.insert_text((54, 230), "Key Policy Milestones", fontsize=11)
    milestones = (
        "The adoption of accelerated permitting protocols in Europe and expanded tax credits under the Inflation "
        "Reduction Act in the United States catalyzed capital expenditure. Global solar manufacturing capacity "
        "reached 500 GW in 2023, while battery storage deployment increased by over 40 percent year-over-year."
    )
    rect2 = pymupdf.Rect(54, 245, 558, 320)
    page1.insert_textbox(rect2, milestones, fontsize=10, lineheight=1.4)
    page1.insert_text((54, 750), "Printed Page: 1 | Global Energy Outlook 2024", fontsize=8)

    # --- PAGE 2: Structured Investment Table ---
    page2 = doc.new_page(width=612, height=792)
    page2.insert_text((54, 60), "2. CAPITAL EXPENDITURE BY TECHNOLOGY", fontsize=12)

    table_title = "Table 1. Global Clean Energy Investment by Technology (Billion USD)"
    page2.insert_text((54, 90), table_title, fontsize=10)

    # Draw table borders and rows
    t_rect = pymupdf.Rect(54, 105, 558, 245)
    page2.draw_rect(t_rect, color=(0.1, 0.2, 0.3), width=1)
    page2.draw_line((54, 135), (558, 135), color=(0.1, 0.2, 0.3), width=1)

    page2.draw_line((240, 105), (240, 245), color=(0.1, 0.2, 0.3), width=0.8)
    page2.draw_line((345, 105), (345, 245), color=(0.1, 0.2, 0.3), width=0.8)
    page2.draw_line((450, 105), (450, 245), color=(0.1, 0.2, 0.3), width=0.8)

    for y in [165, 195, 220]:
        page2.draw_line((54, y), (558, y), color=(0.7, 0.7, 0.7), width=0.5)

    # Table Headers
    page2.insert_text((60, 125), "Technology Sector", fontsize=9)
    page2.insert_text((250, 125), "2021 (USD B)", fontsize=9)
    page2.insert_text((355, 125), "2022 (USD B)", fontsize=9)
    page2.insert_text((460, 125), "2023 (USD B)", fontsize=9)

    # Table Row 1: Solar
    page2.insert_text((60, 155), "Solar PV", fontsize=9)
    page2.insert_text((250, 155), "155", fontsize=9)
    page2.insert_text((355, 155), "210", fontsize=9)
    page2.insert_text((460, 155), "260", fontsize=9)

    # Table Row 2: Wind
    page2.insert_text((60, 185), "Wind Power", fontsize=9)
    page2.insert_text((250, 185), "140", fontsize=9)
    page2.insert_text((355, 185), "175", fontsize=9)
    page2.insert_text((460, 185), "195", fontsize=9)

    # Table Row 3: Grid & Storage
    page2.insert_text((60, 210), "Power Grid & Storage", fontsize=9)
    page2.insert_text((250, 210), "280", fontsize=9)
    page2.insert_text((355, 210), "310", fontsize=9)
    page2.insert_text((460, 210), "350", fontsize=9)

    # Table Row 4: EVs
    page2.insert_text((60, 235), "Electric Vehicles", fontsize=9)
    page2.insert_text((250, 235), "85", fontsize=9)
    page2.insert_text((355, 235), "130", fontsize=9)
    page2.insert_text((460, 235), "180", fontsize=9)

    # Table Footnotes
    footnote_text = "* Note: All financial figures are denominated in billion USD. Projections only extend through 2025. Sources: BNEF, IEA."
    page2.insert_text((54, 265), footnote_text, fontsize=8)

    narrative_p2 = (
        "Solar PV investment exhibited the highest compound annual growth rate among generation assets, "
        "expanding from 210 billion USD in 2022 to 260 billion USD in 2023. Grid modernizations captured "
        "the single largest aggregate share of capital expenditure at 350 billion USD."
    )
    rect3 = pymupdf.Rect(54, 295, 558, 380)
    page2.insert_textbox(rect3, narrative_p2, fontsize=10, lineheight=1.4)
    page2.insert_text((54, 750), "Printed Page: 2 | Global Energy Outlook 2024", fontsize=8)

    doc.save(output_path)
    doc.close()
    return output_path


def create_sample_fiscal_pdf(output_path: Path) -> Path:
    doc = pymupdf.open()

    # --- PAGE 1: Fiscal Overview ---
    page1 = doc.new_page(width=612, height=792)
    page1.insert_text((54, 60), "FEDERAL FISCAL & ECONOMIC PERFORMANCE REPORT FY2023", fontsize=14)
    page1.insert_text((54, 82), "Treasury Department Statistical Bulletin - Annual Report Series", fontsize=10)
    page1.draw_line((54, 92), (558, 92), color=(0.1, 0.3, 0.2), width=1.5)

    page1.insert_text((54, 120), "1. FISCAL YEAR RESULTS OVERVIEW", fontsize=12)
    summary_text = (
        "During fiscal year 2023, the federal government collected 4,441 billion USD in total receipts "
        "and incurred total outlays of 6,134 billion USD, producing an annual fiscal deficit of 1,693 billion USD. "
        "The deficit widened by 320 billion USD compared to the previous fiscal year deficit of 1,373 billion USD. "
        "Interest payments on the public debt rose significantly due to elevated monetary policy rate adjustments."
    )
    rect1 = pymupdf.Rect(54, 135, 558, 220)
    page1.insert_textbox(rect1, summary_text, fontsize=10, lineheight=1.4)
    page1.insert_text((54, 750), "Printed Page: 1 | Federal Fiscal Report FY2023", fontsize=8)

    # --- PAGE 2: Receipts Table ---
    page2 = doc.new_page(width=612, height=792)
    page2.insert_text((54, 60), "2. RECEIPTS BREAKDOWN BY REVENUE CATEGORY", fontsize=12)

    table_title = "Table 2. Federal Government Receipts by Source (Billion USD)"
    page2.insert_text((54, 90), table_title, fontsize=10)

    # Table rectangle
    t_rect = pymupdf.Rect(54, 105, 558, 245)
    page2.draw_rect(t_rect, color=(0.1, 0.2, 0.1), width=1)
    page2.draw_line((54, 135), (558, 135), color=(0.1, 0.2, 0.1), width=1)

    page2.draw_line((260, 105), (260, 245), color=(0.1, 0.2, 0.1), width=0.8)
    page2.draw_line((355, 105), (355, 245), color=(0.1, 0.2, 0.1), width=0.8)
    page2.draw_line((455, 105), (455, 245), color=(0.1, 0.2, 0.1), width=0.8)

    for y in [165, 195, 220]:
        page2.draw_line((54, y), (558, y), color=(0.7, 0.7, 0.7), width=0.5)

    # Headers
    page2.insert_text((60, 125), "Receipts Source", fontsize=9)
    page2.insert_text((270, 125), "2021 (USD B)", fontsize=9)
    page2.insert_text((365, 125), "2022 (USD B)", fontsize=9)
    page2.insert_text((465, 125), "2023 (USD B)", fontsize=9)

    # Rows
    page2.insert_text((60, 155), "Individual Income Taxes", fontsize=9)
    page2.insert_text((270, 155), "2,044", fontsize=9)
    page2.insert_text((365, 155), "2,632", fontsize=9)
    page2.insert_text((465, 155), "2,176", fontsize=9)

    page2.insert_text((60, 185), "Corporation Income Taxes", fontsize=9)
    page2.insert_text((270, 185), "372", fontsize=9)
    page2.insert_text((365, 185), "425", fontsize=9)
    page2.insert_text((465, 185), "420", fontsize=9)

    page2.insert_text((60, 210), "Social Insurance & Retirement", fontsize=9)
    page2.insert_text((270, 210), "1,311", fontsize=9)
    page2.insert_text((365, 210), "1,484", fontsize=9)
    page2.insert_text((465, 210), "1,614", fontsize=9)

    page2.insert_text((60, 235), "Excise Taxes", fontsize=9)
    page2.insert_text((270, 235), "75", fontsize=9)
    page2.insert_text((365, 235), "88", fontsize=9)
    page2.insert_text((465, 235), "76", fontsize=9)

    # Footnote
    page2.insert_text((54, 265), "* Note: Denominated in billion USD. Fiscal year ends September 30. Source: Department of the Treasury.", fontsize=8)

    narrative_p2 = (
        "Individual income tax collections declined by 456 billion USD between 2022 and 2023, reflecting "
        "moderating asset valuations and lower realized capital gains. Conversely, social insurance receipts "
        "grew from 1,484 billion USD to 1,614 billion USD due to continued labor market wage gains."
    )
    rect2 = pymupdf.Rect(54, 295, 558, 380)
    page2.insert_textbox(rect2, narrative_p2, fontsize=10, lineheight=1.4)
    page2.insert_text((54, 750), "Printed Page: 2 | Federal Fiscal Report FY2023", fontsize=8)

    doc.save(output_path)
    doc.close()
    return output_path


def seed_sample_documents(registry: DocumentRegistry) -> list[str]:
    sample_dir = registry.upload_dir / "samples"
    sample_dir.mkdir(parents=True, exist_ok=True)

    # 1. Global Clean Energy Report 2024
    energy_pdf_path = sample_dir / "global_energy_outlook_2024.pdf"
    create_sample_energy_pdf(energy_pdf_path)
    doc_id_1 = "doc_sample_energy_2024"
    if doc_id_1 not in registry.documents:
        registry.register_file(energy_pdf_path, "global_energy_outlook_2024.pdf", doc_id=doc_id_1)

    # 2. Federal Fiscal Report FY2023
    fiscal_pdf_path = sample_dir / "federal_fiscal_report_fy2023.pdf"
    create_sample_fiscal_pdf(fiscal_pdf_path)
    doc_id_2 = "doc_sample_fiscal_2023"
    if doc_id_2 not in registry.documents:
        registry.register_file(fiscal_pdf_path, "federal_fiscal_report_fy2023.pdf", doc_id=doc_id_2)

    return [doc_id_1, doc_id_2]
