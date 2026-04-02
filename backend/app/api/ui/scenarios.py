from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...models.ui_scenario import UIScenario
from ...schemas.task import ScenarioCreate, ScenarioResponse

router = APIRouter(prefix="/ui/scenarios", tags=["UI场景"])


@router.post("/", response_model=ScenarioResponse)
async def create_ui_scenario(
    scenario: ScenarioCreate,
    db: Session = Depends(get_db)
):
    new_scenario = UIScenario(**scenario.dict())
    db.add(new_scenario)
    db.commit()
    db.refresh(new_scenario)
    return new_scenario


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_ui_scenario(scenario_id: str, db: Session = Depends(get_db)):
    scenario = db.query(UIScenario).filter(UIScenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")
    return scenario