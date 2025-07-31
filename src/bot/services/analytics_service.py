import logging
from io import BytesIO
from datetime import date, timedelta
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from matplotlib import pyplot as plt, dates as mdates

# Note: We need to import from the new repositories path
from src.bot.database.repositories import AnalyticsRepository, SchedulerRepository


logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, bot: Bot, repository: AnalyticsRepository, scheduler_repository: SchedulerRepository):
        self.bot = bot
        self.repository = repository
        self.scheduler_repository = scheduler_repository

    # ... existing get_post_views method ...

    async def create_views_chart(
        self, user_id: int, channel_id: Optional[int] = None, days: int = 30
    ) -> Optional[BytesIO]:
        """
        Generates a line chart of total daily views for a user's channels.
        Can be filtered by a specific channel_id.
        """
        daily_views = await self.repository.get_daily_views(user_id, days, channel_id)

        if not daily_views:
            return None

        # Prepare data for plotting, filling in days with no views
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)
        all_dates = [start_date + timedelta(days=i) for i in range(days)]
        
        views_dict = {d: v for d, v in daily_views}
        views_data = [views_dict.get(d, 0) for d in all_dates]

        # Create the plot using matplotlib
        plt.style.use('seaborn-v0_8-darkgrid')
        fig, ax = plt.subplots(figsize=(12, 7))

        ax.plot(all_dates, views_data, marker='o', linestyle='-', color='deepskyblue')
        ax.fill_between(all_dates, views_data, color='deepskyblue', alpha=0.1)

        # Formatting the plot for a nice look
        ax.set_title(f'Total Post Views Over Last {days} Days', fontsize=16, pad=20)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Total Views', fontsize=12)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days // 7)))
        fig.autofmt_xdate()
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.tight_layout()

        # Save plot to a bytes buffer instead of a file
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        plt.close(fig)

        return buf
