"""
Secure Recurrence Calculation Module for PixelCast Signage Digital Signage System.

Provides accurate recurrence calculation for schedules using python-dateutil.rrule.
Includes security measures to prevent injection attacks and validate inputs.
"""

import logging
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.core.exceptions import ValidationError

# Try to import pytz for timezone handling (optional)
try:
    import pytz
except ImportError:
    pytz = None

logger = logging.getLogger(__name__)


class RecurrenceError(Exception):
    """Custom exception for recurrence-related errors."""
    pass


class SecureRecurrenceCalculator:
    """
    Secure recurrence calculator with input validation and injection prevention.
    
    Uses python-dateutil.rrule for accurate recurrence calculation, handling:
    - Daily, weekly, and monthly recurrences
    - End-of-month edge cases
    - Leap years
    - DST changes
    - Timezone-aware datetime handling
    """
    
    # Maximum recurrence limit to prevent DoS attacks
    MAX_RECURRENCE_LIMIT = 10000
    MAX_YEARS_IN_FUTURE = 10
    
    @staticmethod
    def _validate_datetime(dt: datetime, field_name: str = "datetime") -> None:
        """
        Validate datetime object to prevent injection attacks.
        
        Args:
            dt: Datetime object to validate
            field_name: Name of the field for error messages
            
        Raises:
            ValidationError: If datetime is invalid
        """
        if not isinstance(dt, datetime):
            raise ValidationError(f"{field_name} must be a datetime object")
        
        # Check for reasonable date range (prevent year 9999 attacks)
        if dt.year < 1900 or dt.year > 2100:
            raise ValidationError(
                f"{field_name} year must be between 1900 and 2100"
            )
        
        # Check for valid date components
        try:
            dt.replace()  # This will raise ValueError if date is invalid
        except (ValueError, OverflowError) as e:
            raise ValidationError(f"Invalid {field_name}: {str(e)}")
    
    @staticmethod
    def _validate_repeat_type(repeat_type: str) -> None:
        """
        Validate repeat_type to prevent injection.
        
        Args:
            repeat_type: Repeat type string
            
        Raises:
            ValidationError: If repeat_type is invalid
        """
        allowed_types = ['none', 'daily', 'weekly', 'monthly']
        if repeat_type not in allowed_types:
            raise ValidationError(
                f"Invalid repeat_type: {repeat_type}. "
                f"Must be one of {allowed_types}"
            )
    
    @staticmethod
    def _sanitize_string(value: str, max_length: int = 100) -> str:
        """
        Sanitize string input to prevent injection attacks.
        
        Args:
            value: String to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            raise ValidationError("Value must be a string")
        
        # Remove any null bytes and control characters
        sanitized = ''.join(c for c in value if ord(c) >= 32 or c in '\t\n\r')
        
        # Limit length
        if len(sanitized) > max_length:
            raise ValidationError(f"String exceeds maximum length of {max_length}")
        
        return sanitized
    
    @classmethod
    def calculate_next_run(
        cls,
        start_time: datetime,
        end_time: datetime,
        repeat_type: str,
        last_executed_at: Optional[datetime] = None,
        reference_time: Optional[datetime] = None
    ) -> Optional[datetime]:
        """
        Calculate the next scheduled run time using accurate recurrence rules.
        
        Args:
            start_time: Initial start time of the schedule
            end_time: Initial end time of the schedule
            repeat_type: Type of recurrence ('none', 'daily', 'weekly', 'monthly')
            last_executed_at: Last time the schedule was executed (optional)
            reference_time: Reference time for calculation (defaults to now)
            
        Returns:
            Next scheduled run time, or None if no more occurrences
            
        Raises:
            RecurrenceError: If calculation fails
            ValidationError: If inputs are invalid
        """
        # Validate inputs
        cls._validate_datetime(start_time, "start_time")
        cls._validate_datetime(end_time, "end_time")
        cls._validate_repeat_type(repeat_type)
        
        if end_time <= start_time:
            raise ValidationError("end_time must be after start_time")
        
        # Use reference time or current time
        if reference_time is None:
            reference_time = timezone.now()
        else:
            cls._validate_datetime(reference_time, "reference_time")
        
        # Ensure timezone awareness
        if timezone.is_naive(start_time):
            start_time = timezone.make_aware(start_time)
        if timezone.is_naive(end_time):
            end_time = timezone.make_aware(end_time)
        if timezone.is_naive(reference_time):
            reference_time = timezone.make_aware(reference_time)
        
        # For one-time schedules
        if repeat_type == 'none':
            if start_time > reference_time:
                return start_time
            return None
        
        # Calculate duration of schedule window
        duration = end_time - start_time
        
        # For recurring schedules, find next occurrence
        try:
            if repeat_type == 'daily':
                # Daily recurrence: same time every day
                rrule_obj = rrule.rrule(
                    rrule.DAILY,
                    dtstart=start_time,
                    until=reference_time + timedelta(days=365 * cls.MAX_YEARS_IN_FUTURE),
                    count=cls.MAX_RECURRENCE_LIMIT
                )
                
            elif repeat_type == 'weekly':
                # Weekly recurrence: same day of week and time
                rrule_obj = rrule.rrule(
                    rrule.WEEKLY,
                    dtstart=start_time,
                    until=reference_time + timedelta(days=365 * cls.MAX_YEARS_IN_FUTURE),
                    count=cls.MAX_RECURRENCE_LIMIT
                )
                
            elif repeat_type == 'monthly':
                # Monthly recurrence: same day of month and time
                # Handle end-of-month edge cases (e.g., Jan 31 -> Feb 28/29)
                rrule_obj = rrule.rrule(
                    rrule.MONTHLY,
                    dtstart=start_time,
                    until=reference_time + timedelta(days=365 * cls.MAX_YEARS_IN_FUTURE),
                    count=cls.MAX_RECURRENCE_LIMIT,
                    bymonthday=start_time.day
                )
            else:
                raise RecurrenceError(f"Unsupported repeat_type: {repeat_type}")
            
            # Get all occurrences after reference time
            occurrences = list(rrule_obj)
            next_occurrence = None
            
            for occurrence in occurrences:
                if occurrence > reference_time:
                    next_occurrence = occurrence
                    break
            
            return next_occurrence
            
        except Exception as e:
            logger.error(f"Error calculating next run: {str(e)}")
            raise RecurrenceError(f"Failed to calculate next run: {str(e)}")
    
    @classmethod
    def is_running_now(
        cls,
        start_time: datetime,
        end_time: datetime,
        repeat_type: str,
        reference_time: Optional[datetime] = None
    ) -> bool:
        """
        Check if schedule should be running at the given reference time.
        
        Args:
            start_time: Initial start time of the schedule
            end_time: Initial end time of the schedule
            repeat_type: Type of recurrence
            reference_time: Reference time to check (defaults to now)
            
        Returns:
            True if schedule should be running, False otherwise
        """
        # Validate inputs
        cls._validate_datetime(start_time, "start_time")
        cls._validate_datetime(end_time, "end_time")
        cls._validate_repeat_type(repeat_type)
        
        if reference_time is None:
            reference_time = timezone.now()
        else:
            cls._validate_datetime(reference_time, "reference_time")
        
        # Ensure timezone awareness
        if timezone.is_naive(start_time):
            start_time = timezone.make_aware(start_time)
        if timezone.is_naive(end_time):
            end_time = timezone.make_aware(end_time)
        if timezone.is_naive(reference_time):
            reference_time = timezone.make_aware(reference_time)
        
        # For one-time schedules
        if repeat_type == 'none':
            return start_time <= reference_time <= end_time
        
        # Calculate duration
        duration = end_time - start_time
        
        # For recurring schedules, check if reference_time falls within any occurrence
        try:
            if repeat_type == 'daily':
                # Check if same time window today
                start_time_today = reference_time.replace(
                    hour=start_time.hour,
                    minute=start_time.minute,
                    second=start_time.second,
                    microsecond=start_time.microsecond
                )
                end_time_today = start_time_today + duration
                return start_time_today <= reference_time <= end_time_today
                
            elif repeat_type == 'weekly':
                # Check if same day of week and within time window
                if reference_time.weekday() == start_time.weekday():
                    start_time_this_week = reference_time.replace(
                        hour=start_time.hour,
                        minute=start_time.minute,
                        second=start_time.second,
                        microsecond=start_time.microsecond
                    )
                    end_time_this_week = start_time_this_week + duration
                    return start_time_this_week <= reference_time <= end_time_this_week
                return False
                
            elif repeat_type == 'monthly':
                # Check if same day of month and within time window
                # Handle end-of-month: if start is Jan 31 and today is Feb 28, check Feb 28
                try:
                    start_time_this_month = reference_time.replace(
                        day=start_time.day,
                        hour=start_time.hour,
                        minute=start_time.minute,
                        second=start_time.second,
                        microsecond=start_time.microsecond
                    )
                except ValueError:
                    # Day doesn't exist in this month (e.g., Jan 31 -> Feb 28/29)
                    # Use last day of month
                    last_day = (reference_time.replace(day=1) + relativedelta(months=1) - timedelta(days=1)).day
                    start_time_this_month = reference_time.replace(
                        day=min(start_time.day, last_day),
                        hour=start_time.hour,
                        minute=start_time.minute,
                        second=start_time.second,
                        microsecond=start_time.microsecond
                    )
                
                end_time_this_month = start_time_this_month + duration
                return start_time_this_month <= reference_time <= end_time_this_month
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking if running now: {str(e)}")
            return False
    
    @classmethod
    def get_occurrences_in_range(
        cls,
        start_time: datetime,
        end_time: datetime,
        repeat_type: str,
        range_start: datetime,
        range_end: datetime,
        max_occurrences: int = 1000
    ) -> List[datetime]:
        """
        Get all schedule occurrences within a time range.
        Useful for conflict detection.
        
        Args:
            start_time: Initial start time of the schedule
            end_time: Initial end time of the schedule
            repeat_type: Type of recurrence
            range_start: Start of time range to check
            range_end: End of time range to check
            max_occurrences: Maximum number of occurrences to return
            
        Returns:
            List of occurrence start times within the range
        """
        # Validate inputs
        cls._validate_datetime(start_time, "start_time")
        cls._validate_datetime(end_time, "end_time")
        cls._validate_datetime(range_start, "range_start")
        cls._validate_datetime(range_end, "range_end")
        cls._validate_repeat_type(repeat_type)
        
        if range_end <= range_start:
            raise ValidationError("range_end must be after range_start")
        
        if repeat_type == 'none':
            # Single occurrence
            if range_start <= start_time <= range_end:
                return [start_time]
            return []
        
        # Ensure timezone awareness
        if timezone.is_naive(start_time):
            start_time = timezone.make_aware(start_time)
        if timezone.is_naive(range_start):
            range_start = timezone.make_aware(range_start)
        if timezone.is_naive(range_end):
            range_end = timezone.make_aware(range_end)
        
        try:
            # Generate recurrence rule
            if repeat_type == 'daily':
                rrule_obj = rrule.rrule(
                    rrule.DAILY,
                    dtstart=start_time,
                    until=range_end,
                    count=min(max_occurrences, cls.MAX_RECURRENCE_LIMIT)
                )
            elif repeat_type == 'weekly':
                rrule_obj = rrule.rrule(
                    rrule.WEEKLY,
                    dtstart=start_time,
                    until=range_end,
                    count=min(max_occurrences, cls.MAX_RECURRENCE_LIMIT)
                )
            elif repeat_type == 'monthly':
                rrule_obj = rrule.rrule(
                    rrule.MONTHLY,
                    dtstart=start_time,
                    until=range_end,
                    count=min(max_occurrences, cls.MAX_RECURRENCE_LIMIT),
                    bymonthday=start_time.day
                )
            else:
                return []
            
            # Get occurrences in range
            occurrences = []
            for occurrence in rrule_obj:
                if occurrence < range_start:
                    continue
                if occurrence > range_end:
                    break
                occurrences.append(occurrence)
                if len(occurrences) >= max_occurrences:
                    break
            
            return occurrences
            
        except Exception as e:
            logger.error(f"Error getting occurrences in range: {str(e)}")
            return []
    
    @classmethod
    def check_overlap(
        cls,
        start1: datetime,
        end1: datetime,
        start2: datetime,
        end2: datetime,
        repeat_type1: str,
        repeat_type2: str,
        check_range_start: datetime,
        check_range_end: datetime
    ) -> bool:
        """
        Check if two recurring schedules overlap within a time range.
        
        Args:
            start1, end1: First schedule's initial time window
            start2, end2: Second schedule's initial time window
            repeat_type1, repeat_type2: Recurrence types
            check_range_start, check_range_end: Time range to check for overlaps
            
        Returns:
            True if schedules overlap, False otherwise
        """
        # Get all occurrences for both schedules in the check range
        occurrences1 = cls.get_occurrences_in_range(
            start1, end1, repeat_type1, check_range_start, check_range_end
        )
        occurrences2 = cls.get_occurrences_in_range(
            start2, end2, repeat_type2, check_range_start, check_range_end
        )
        
        # Calculate durations
        duration1 = end1 - start1
        duration2 = end2 - start2
        
        # Check for overlaps
        for occ1 in occurrences1:
            occ1_end = occ1 + duration1
            for occ2 in occurrences2:
                occ2_end = occ2 + duration2
                # Overlap if: occ1 < occ2_end AND occ2 < occ1_end
                if occ1 < occ2_end and occ2 < occ1_end:
                    return True
        
        return False

