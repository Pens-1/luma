from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .plugins.weather_clothing import router as weather_router

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the weather clothing plugin router
app.include_router(weather_router)

@app.get("/bot")
async def handle_bot_action(action: str):
    if action.startswith("[ACTION:WEATHER:"):
        # Extract day index from the action
        try:
            day_index = int(action.split(":")[2])
        except (ValueError, IndexError):
            return {"error": "Invalid action format."}

        # Call the weather clothing endpoint with the extracted day index
        return await weather_router.get_weather_and_clothing(lat=35.6895, lon=139.6917, day_index=day_index)

    return {"error": "Unsupported action."}
