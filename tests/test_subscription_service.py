import pytest
from unittest.mock import AsyncMock, MagicMock

# Test qilinadigan servis va unga bog'liq qismlarni import qilamiz
from src.bot.services.subscription_service import SubscriptionService
from src.bot.database.repositories import UserRepository, PlanRepository, ChannelRepository, SchedulerRepository
from src.bot.config import Settings

# Pytest sozlamasi
pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_settings() -> Settings:
    """Soxta `settings` obyekti. Cheklovlar yoqilgan deb hisoblaymiz."""
    settings = MagicMock(spec=Settings)
    settings.ENFORCE_PLAN_LIMITS = True
    return settings

@pytest.fixture
def mock_user_repo() -> AsyncMock:
    """Soxta UserRepository."""
    return AsyncMock(spec=UserRepository)

@pytest.fixture
def mock_plan_repo() -> AsyncMock:
    """Soxta PlanRepository."""
    return AsyncMock(spec=PlanRepository)

@pytest.fixture
def mock_channel_repo() -> AsyncMock:
    """Soxta ChannelRepository."""
    return AsyncMock(spec=ChannelRepository)

@pytest.fixture
def mock_scheduler_repo() -> AsyncMock:
    """Soxta SchedulerRepository."""
    return AsyncMock(spec=SchedulerRepository)


@pytest.fixture
def subscription_service(
    mock_settings,
    mock_user_repo,
    mock_plan_repo,
    mock_channel_repo,
    mock_scheduler_repo
) -> SubscriptionService:
    """Test uchun tayyorlangan SubscriptionService instansi."""
    return SubscriptionService(
        settings=mock_settings,
        user_repo=mock_user_repo,
        plan_repo=mock_plan_repo,
        channel_repo=mock_channel_repo,
        scheduler_repo=mock_scheduler_repo,
    )


async def test_check_channel_limit_allow(subscription_service: SubscriptionService, mock_user_repo, mock_plan_repo, mock_channel_repo):
    """Foydalanuvchi kanal qo'sha olishi kerak (limitdan oshmagan)."""
    # Soxta ma'lumotlarni tayyorlaymiz
    mock_user_repo.get_user_plan_name.return_value = "free"
    mock_plan_repo.get_plan_by_name.return_value = {"max_channels": 3}
    mock_channel_repo.count_user_channels.return_value = 2 # 3 tadan 2 ta kanal bor

    # Servis metodini chaqiramiz va natijani tekshiramiz
    can_add = await subscription_service.check_channel_limit(user_id=123)
    assert can_add is True


async def test_check_channel_limit_deny(subscription_service: SubscriptionService, mock_user_repo, mock_plan_repo, mock_channel_repo):
    """Foydalanuvchi kanal qo'sha olmasligi kerak (limitga yetgan)."""
    mock_user_repo.get_user_plan_name.return_value = "free"
    mock_plan_repo.get_plan_by_name.return_value = {"max_channels": 3}
    mock_channel_repo.count_user_channels.return_value = 3 # 3 tadan 3 ta kanal bor

    can_add = await subscription_service.check_channel_limit(user_id=123)
    assert can_add is False

async def test_check_channel_limit_unlimited(subscription_service: SubscriptionService, mock_user_repo, mock_plan_repo):
    """Foydalanuvchi cheksiz kanal qo'sha olishi kerak."""
    mock_user_repo.get_user_plan_name.return_value = "premium"
    mock_plan_repo.get_plan_by_name.return_value = {"max_channels": -1} # Cheksiz

    can_add = await subscription_service.check_channel_limit(user_id=123)
    assert can_add is True

# Post limitlari uchun ham shunga o'xshash testlarni yozish mumkin...
