from aiogram import Router

from bot.handlers.common import router as common_router
from bot.handlers.auth import router as auth_router
from bot.handlers.tasks import router as tasks_router
from bot.handlers.ai import router as ai_router
from bot.handlers.profile import router as profile_router


router = Router()

router.include_router(common_router)
router.include_router(auth_router)
router.include_router(tasks_router)
router.include_router(ai_router)
router.include_router(profile_router)