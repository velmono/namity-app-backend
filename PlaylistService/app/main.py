from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.playlists import router as playlists_router

app = FastAPI(title="Namity-Playlist")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(playlists_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8004, reload=True) 