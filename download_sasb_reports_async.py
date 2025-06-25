import os
import asyncio
import aiohttp
import aiofiles
import pandas as pd

PDF_FOLDER = "company_reports_pdfs"
CSV_INPUT = "sasb_reporters_metadata.csv"
CSV_SUCCESS = "downloaded_successfully.csv"
CSV_FAILED = "download_failed.csv"
URL_COLUMN = "PDF URL"

# Ensure the PDF folder exists
os.makedirs(PDF_FOLDER, exist_ok=True)

def extract_filename_from_url(url):
    return url.split("/")[-1].split("?")[0]

async def download_pdf(session, url):
    if pd.isna(url) or not url.lower().endswith(".pdf"):
        return None, "Invalid or missing URL"

    filename = extract_filename_from_url(url)
    filepath = os.path.join(PDF_FOLDER, filename)

    if os.path.exists(filepath):
        return filename, "Already exists"

    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(filepath, mode='wb')
                await f.write(await resp.read())
                await f.close()
                return filename, "Downloaded"
            else:
                return None, f"HTTP {resp.status}"
    except Exception as e:
        return None, str(e)

async def process_all():
    df = pd.read_csv(CSV_INPUT)
    downloaded_rows = []
    failed_rows = []

    async with aiohttp.ClientSession() as session:
        for i, row in df.iterrows():
            url = row.get(URL_COLUMN)
            filename, status = await download_pdf(session, url)

            if filename:
                row["PDF Name"] = filename
                downloaded_rows.append(row)
            else:
                row["Error"] = status
                failed_rows.append(row)

            print(f"{i+1}/{len(df)}: {row.get('Company name')} => {status}")

    # Save results
    pd.DataFrame(downloaded_rows).to_csv(CSV_SUCCESS, index=False)
    pd.DataFrame(failed_rows).to_csv(CSV_FAILED, index=False)
    print(f"\n✅ Finished:\n - Success: {len(downloaded_rows)}\n - Failed: {len(failed_rows)}")

if __name__ == "__main__":
    asyncio.run(process_all())
