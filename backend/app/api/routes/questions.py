from fastapi import APIRouter
from backend.app.pipeline.engine import ReportIntelligenceEngine
from backend.app.schemas.question import AnswerResponse, QuestionRequest

router = APIRouter(prefix="/questions", tags=["questions"])

_engine: ReportIntelligenceEngine | None = None

def get_engine() -> ReportIntelligenceEngine:
    global _engine
    if _engine is None:
        _engine = ReportIntelligenceEngine()
    return _engine

@router.post("", response_model=AnswerResponse)
def ask_question(request: QuestionRequest) -> AnswerResponse:
    engine = get_engine()
    return engine.answer_question(request)

