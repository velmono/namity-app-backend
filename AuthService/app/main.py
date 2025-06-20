import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.auth import router as auth_router
from app.dependencies import get_current_user
from app.schemas import UserRead

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url="/openapi.json",
)

# CORS если нужен
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Роутер
app.include_router(auth_router)

#Защищенный маршрут для получения информации о текущем пользователе
@app.get("/me", response_model=UserRead, tags=["auth"])
async def read_current_user(
    current_user = Depends(get_current_user)
) -> UserRead:
    return current_user


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
