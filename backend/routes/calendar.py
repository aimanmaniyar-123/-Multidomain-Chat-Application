from fastapi import APIRouter

router = APIRouter()

@router.get("/calendar-events")
async def get_mock_events():
    return {
        "events": [
            {"summary": "Team Sync", "start": "2025-08-05T10:00", "end": "2025-08-05T11:00"},
            {"summary": "Client Call", "start": "2025-08-06T14:00", "end": "2025-08-06T15:00"}
        ]
    }
