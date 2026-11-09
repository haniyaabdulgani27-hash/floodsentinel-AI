import fitz
from pathlib import Path

pdf_path = Path("ml/dataset/geospatial/flood_extent/assam_flood_hazard_atlas.pdf")

doc = fitz.open(pdf_path)

districts = ["Darrang", "Udalguri", "Kamrup Metropolitan"]

for district in districts:
    print(f"\n{'='*50}")
    print("DISTRICT:", district)
    print("=" * 50)

    matches = 0

    for page_num, page in enumerate(doc):
        text = page.get_text()

        if district.lower() in text.lower():
            print(f"\nPage {page_num + 1}:")
            print(text[:2500])
            matches += 1

            if matches >= 5:
                break

    if matches == 0:
        print("No text match found.")
