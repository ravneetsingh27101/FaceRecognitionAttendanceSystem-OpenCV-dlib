from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from api.auth import router as auth_router
from api.routers.subjects import router as subjects_router
from api.routers.students import router as students_router
from api.routers.attendance import router as attendance_router
from api.routers.training import router as training_router
from api.routers.reports import router as reports_router
from api.routers.web import router as web_router

app = FastAPI(title="FRAS API")
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(subjects_router, prefix="/subjects", tags=["subjects"])
app.include_router(students_router, prefix="/students", tags=["students"])
app.include_router(attendance_router, prefix="/attendance", tags=["attendance"])
app.include_router(training_router, prefix="/train", tags=["training"])
app.include_router(reports_router, prefix="/reports", tags=["reports"])
app.include_router(web_router, prefix="/web", tags=["web"])

# Serve the modern web UI (gui 2.0) as static files
app.mount("/app", StaticFiles(directory="gui 2.0", html=True), name="webapp")

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/")
def root():
    # Redirect to the SPA
    return RedirectResponse(url="/app/index.html")
