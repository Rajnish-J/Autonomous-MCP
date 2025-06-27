import pandas as pd
from app.core.llm_generator import generate_test_script
from app.core.playwright_runner import run_test_code
import tempfile

async def process_excel_file(file):
    df = pd.read_excel(file.file)
    report = []

    for idx, row in df.iterrows():
        description = row['TestCase']
        code = await generate_test_script(description)
        result = await run_test_code(code)
        report.append({
            'TestCase': description,
            'Status': result
        })

    return report
