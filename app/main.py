from fastapi import FastAPI
from app.config import settings
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine, SessionLocal
from app import models
from app.router import auth, admin,hospital,donor,requester
from app.router.auth import bcrypt_context

app = FastAPI()
models.Base.metadata.create_all(bind=engine)


def create_admin():
    db = SessionLocal()

    try:

        admin_exists =(db.query(models.Users).filter(models.Users.role=="admin").first())

        if admin_exists:
            return

        
        admin = models.Users(
            username="Admin",
            email=settings.admin_email,
            hashed_password=bcrypt_context.hash(settings.admin_password),
            role="admin",
            is_verified=True,
            is_active=True,
        )

        db.add(admin)
        db.commit()

    finally:
        db.close()

create_admin()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(hospital.router)
app.include_router(donor.router)
app.include_router(requester.router)


@app.get("/")
def health():
    return {"status": "ok"}
