import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import bookings, clients, config, schedule, services, admin
from app.bot.bot import bot, dp
from app.bot.handlers import start as start_handler
from app.bot.handlers import booking as booking_handler
from app.bot.handlers import admin as admin_handler
from app.config import settings
from app.database import engine, Base, async_session
from app.services.schedule_service import ScheduleService
from app.tasks.reminders import check_followups, check_reminders

STATIC_DIR = Path(__file__).parent.parent / "static"

scheduler = AsyncIOScheduler()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Initialize default schedule
    async with async_session() as session:
        svc = ScheduleService(session)
        await svc.init_default_schedule()

    # Seed default services if empty
    from sqlalchemy import select, func
    from app.models.service import Service

    async with async_session() as session:
        count = await session.execute(select(func.count(Service.id)))
        if count.scalar() == 0:
            defaults = [
                Service(
                    name="Гигиенический маникюр",
                    description="Коррекция формы, удаление ножницами кутикулы и её шлифовка, очистка боковых валиков, удаление заусенцев, увлажнение кожи рук и зоны кутикулы маслом.",
                    duration_minutes=40,
                    price=30,
                    sort_order=1,
                ),
                Service(
                    name="Аппаратный маникюр + японский уход",
                    description="Аппаратная обработка кутикулы и боковых валиков, коррекция формы, шлифовка ногтевой пластины, втирание минеральной пасты, пудры для блеска и защиты, увлажнение маслом, массаж рук кремом.",
                    duration_minutes=60,
                    price=40,
                    sort_order=2,
                ),
                Service(
                    name="Маникюр с покрытием гель-лака",
                    description="Аппаратная обработка зоны кутикулы и боковых валиков, коррекция формы, подготовка ногтевой пластины, нанесение базы, выравнивание гелем, цветное покрытие, нанесение топа, увлажнение кожи рук.",
                    duration_minutes=90,
                    price=50,
                    sort_order=3,
                ),
            ]
            session.add_all(defaults)
            await session.commit()


async def start_bot():
    dp.include_router(start_handler.router)
    dp.include_router(booking_handler.router)
    dp.include_router(admin_handler.router)
    asyncio.create_task(dp.start_polling(bot))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await start_bot()

    # Schedule reminders
    scheduler.add_job(check_reminders, "interval", minutes=15)
    scheduler.add_job(check_followups, "interval", minutes=30)
    scheduler.start()

    yield

    scheduler.shutdown()
    await bot.session.close()


app = FastAPI(title="DAINA Nail Studio", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(services.router)
app.include_router(bookings.router)
app.include_router(clients.router)
app.include_router(schedule.router)
app.include_router(admin.router)
app.include_router(config.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}


# Serve frontend static files (built React app)
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """Serve React SPA — all non-API routes return index.html."""
        file_path = STATIC_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
