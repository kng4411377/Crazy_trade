"""Market hours checking utilities using pandas_market_calendars."""

from datetime import datetime, time, timedelta
from typing import Optional
import pandas_market_calendars as mcal
import pytz
import structlog

logger = structlog.get_logger()


class MarketHoursChecker:
    """Check if current time is within regular trading hours."""

    def __init__(self, calendar_name: str = "XNYS", 
                 allow_pre_market: bool = False,
                 allow_after_hours: bool = False):
        """
        Initialize market hours checker.
        
        Args:
            calendar_name: Market calendar name (e.g., "XNYS" for NYSE)
            allow_pre_market: Whether to allow pre-market trading
            allow_after_hours: Whether to allow after-hours trading
        """
        self.calendar_name = calendar_name
        self.allow_pre_market = allow_pre_market
        self.allow_after_hours = allow_after_hours
        
        try:
            self.calendar = mcal.get_calendar(calendar_name)
            logger.info("market_calendar_initialized", calendar=calendar_name)
        except Exception as e:
            logger.error("failed_to_initialize_calendar", calendar=calendar_name, error=str(e))
            raise

        # NYSE regular trading hours (Eastern Time)
        self.rth_open = time(9, 30)
        self.rth_close = time(16, 0)
        self.pre_market_open = time(4, 0)
        self.after_hours_close = time(20, 0)

        self.eastern = pytz.timezone("America/New_York")

    def is_market_open(self, dt: Optional[datetime] = None) -> bool:
        """
        Check if market is open at the given time.
        
        Args:
            dt: Datetime to check (defaults to now in UTC)
            
        Returns:
            True if market is open for trading
        """
        if dt is None:
            dt = datetime.utcnow()
        
        # Convert to Eastern time
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        dt_eastern = dt.astimezone(self.eastern)
        
        # Check if it's a trading day
        date = dt_eastern.date()
        schedule = self.calendar.schedule(start_date=date, end_date=date)
        
        if schedule.empty:
            logger.debug("market_closed_not_trading_day", date=str(date))
            return False
        
        # Check time within allowed hours
        current_time = dt_eastern.time()
        
        # Determine allowed time range
        if self.allow_pre_market:
            start_time = self.pre_market_open
        else:
            start_time = self.rth_open
        
        if self.allow_after_hours:
            end_time = self.after_hours_close
        else:
            end_time = self.rth_close
        
        is_open = start_time <= current_time <= end_time
        
        if not is_open:
            logger.debug("market_closed_outside_hours", 
                        current_time=str(current_time),
                        start_time=str(start_time),
                        end_time=str(end_time))
        
        return is_open

    def is_regular_trading_hours(self, dt: Optional[datetime] = None) -> bool:
        """
        Check if current time is within regular trading hours (9:30 AM - 4:00 PM ET).
        
        Args:
            dt: Datetime to check (defaults to now)
            
        Returns:
            True if within RTH
        """
        if dt is None:
            dt = datetime.utcnow()
        
        # Convert to Eastern time
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        dt_eastern = dt.astimezone(self.eastern)
        
        # Check if it's a trading day
        date = dt_eastern.date()
        schedule = self.calendar.schedule(start_date=date, end_date=date)
        
        if schedule.empty:
            return False
        
        # Check RTH hours
        current_time = dt_eastern.time()
        return self.rth_open <= current_time <= self.rth_close

    def next_market_open(self, dt: Optional[datetime] = None) -> datetime:
        """
        Get the next market open time.
        
        Args:
            dt: Starting datetime (defaults to now)
            
        Returns:
            Next market open datetime in UTC
        """
        if dt is None:
            dt = datetime.utcnow()
        
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        
        dt_eastern = dt.astimezone(self.eastern)
        date = dt_eastern.date()
        
        # Look ahead up to 10 days
        for i in range(10):
            check_date = date + timedelta(days=i)
            schedule = self.calendar.schedule(start_date=check_date, end_date=check_date)
            
            if not schedule.empty:
                # Market opens at 9:30 AM ET on this day
                market_open = self.eastern.localize(
                    datetime.combine(check_date, self.rth_open)
                )
                
                # If we're on the same day and before open, return today's open
                if market_open > dt_eastern:
                    return market_open.astimezone(pytz.utc)
        
        # Fallback: return next week
        next_week = dt_eastern + timedelta(days=7)
        return self.eastern.localize(
            datetime.combine(next_week.date(), self.rth_open)
        ).astimezone(pytz.utc)

    def next_market_close(self, dt: Optional[datetime] = None) -> datetime:
        """
        Get the next market close time.
        
        Args:
            dt: Starting datetime (defaults to now)
            
        Returns:
            Next market close datetime in UTC
        """
        if dt is None:
            dt = datetime.utcnow()
        
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        
        dt_eastern = dt.astimezone(self.eastern)
        date = dt_eastern.date()
        
        # Check today first
        schedule = self.calendar.schedule(start_date=date, end_date=date)
        if not schedule.empty:
            market_close = self.eastern.localize(
                datetime.combine(date, self.rth_close)
            )
            if market_close > dt_eastern:
                return market_close.astimezone(pytz.utc)
        
        # Look ahead for next trading day
        for i in range(1, 10):
            check_date = date + timedelta(days=i)
            schedule = self.calendar.schedule(start_date=check_date, end_date=check_date)
            
            if not schedule.empty:
                market_close = self.eastern.localize(
                    datetime.combine(check_date, self.rth_close)
                )
                return market_close.astimezone(pytz.utc)
        
        # Fallback
        next_week = dt_eastern + timedelta(days=7)
        return self.eastern.localize(
            datetime.combine(next_week.date(), self.rth_close)
        ).astimezone(pytz.utc)

    def seconds_until_market_open(self) -> float:
        """Get seconds until next market open."""
        now = datetime.utcnow()
        next_open = self.next_market_open(now)
        return (next_open - pytz.utc.localize(now)).total_seconds()

    def seconds_until_market_close(self) -> float:
        """Get seconds until next market close."""
        now = datetime.utcnow()
        next_close = self.next_market_close(now)
        return (next_close - pytz.utc.localize(now)).total_seconds()

