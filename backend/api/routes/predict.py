from fastapi import APIRouter, File, UploadFile

from backend.schemas import PredictResponse
from backend.services.prediction import run_prediction
from backend.services.uploads import save_upload

router = APIRouter(prefix="/api/v1", tags=["predict"])


@router.post("/predict", response_model=PredictResponse)
async def predict(file: UploadFile = File(..., description="SAR / spill image (JPG, JPEG, PNG)")) -> PredictResponse:
    """Accept an uploaded image and run the prediction service (model stub for now)."""
    image_id, saved_path = await save_upload(file)
    return run_prediction(saved_path, image_id)
