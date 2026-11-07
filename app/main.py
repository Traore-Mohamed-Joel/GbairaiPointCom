from fastapi import Depends, FastAPI

from pathlib import Path
from fastapi.staticfiles import StaticFiles
from app.dependencies import get_current_user
from app.models.user import User
from app.routers.auth import router as auth_router
from app.routers.groups import router as groups_router
from app.routers.messages import router as messages_router
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="GbairaiPointCom",
    description="Application de discussions en groupes en temps réel.",
    version="1.0.0",
)
app.mount(
    "/static",
    StaticFiles(directory=Path("app/static")),
    name="static",
)
templates = Jinja2Templates(directory="app/templates")

# Routes d'authentification
app.include_router(auth_router)

# Routes des groupes
app.include_router(groups_router)

# Routes des messages
app.include_router(messages_router)


@app.get("/")
def home():
    return {
        "message": "Bienvenue sur GbairaiPointCom !",
        "status": "online",
    }

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={},
    )

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={},
    )

@app.get("/me")
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
    }

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={},
    )

@app.get("/groups/{group_id}/chat", response_class=HTMLResponse)
def group_chat_page(request: Request, group_id: int):
    return templates.TemplateResponse(
        request=request,
        name="group.html",
        context={"group_id": group_id},
    )