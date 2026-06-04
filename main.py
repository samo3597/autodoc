import asyncio
from typing import Dict, Any, List
from fastapi import FastAPI
import httpx
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="Async Part Number Processor")


class PartItem(BaseModel):
    id: int
    partNumber: str


async def fetch_parts_data(parts: List[PartItem]) -> List[Dict[str, Any]]:
    async with httpx.AsyncClient() as client:

        tasks = []
        for item in parts:
            url = f"https://webapi.autodoc.ru/api/manufacturer/{item.id}/sparepart/{item.partNumber}"
            tasks.append(client.get(url))

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        aggregated_results = []

        for item, response in zip(parts, responses):
            result_data = {
                "success": False,
                "id": item.id,
                "partNumber": item.partNumber,
                "error": "",
                "data": {}
            }

            if isinstance(response, Exception):
                result_data["error"] = f"Connection failed, details: {str(response)}"
            else:
                try:
                    _json = response.json()
                    result_data["data"] = {
                        'Производитель': _json.get('manufacturerName'),
                        'Производитель_id': _json.get('manufacturerId'),
                        'Артикул': _json.get('partNumber'),
                        'Наименование': _json.get('partName'),
                        'ОписаниеПоставщика': _json.get('description'),
                        'ВНаличии': _json.get('priceQuantity'),
                        'Цена': _json.get('minimalPrice'),
                        'photo': _json.get('galleryModel').get('imgUrls'),
                    }
                    result_data["success"] = True

                    with open('data/data.txt', 'a') as f:
                        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        f.write(" partNumber: {0}, id: {1},\n".format(_json.get('partNumber'), _json.get('manufacturerId')))

                except Exception:
                    result_data["error"] = f"text_response: {response.text}"
            aggregated_results.append(result_data)
        return aggregated_results


@app.post("/process-parts")
async def process_parts(payload: List[PartItem]):
    result = await fetch_parts_data(payload)
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)