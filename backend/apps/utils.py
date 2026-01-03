"""
Shared utility functions for Elitelupus Staff Toolbox.
"""
from datetime import date, datetime, timedelta
from typing import Union


def get_week_start(reference_date: Union[date, datetime]) -> date:
    """
    Calculate the start of the week (Saturday) for a given date.
    
    The weekly reset happens on Saturday, so weeks run Saturday-Friday.
    
    Args:
        reference_date: A date or datetime to calculate the week start from
        
    Returns:
        The date of the Saturday that starts the week containing reference_date
        
    Example:
        - If reference_date is Monday Jan 5, returns Saturday Jan 3
        - If reference_date is Saturday Jan 3, returns Saturday Jan 3
        - If reference_date is Friday Jan 9, returns Saturday Jan 3
    """
    if isinstance(reference_date, datetime):
        reference_date = reference_date.date()
    
    # Python weekday(): Monday=0, Tuesday=1, ..., Saturday=5, Sunday=6
    # We want Saturday to be day 0 of the week
    # Days since Saturday = (weekday + 2) % 7
    # Monday (0) -> (0+2)%7 = 2 days since Saturday
    # Saturday (5) -> (5+2)%7 = 0 days since Saturday
    # Sunday (6) -> (6+2)%7 = 1 day since Saturday
    # Friday (4) -> (4+2)%7 = 6 days since Saturday
    days_since_saturday = (reference_date.weekday() + 2) % 7
    return reference_date - timedelta(days=days_since_saturday)


def get_week_end(reference_date: Union[date, datetime]) -> date:
    """
    Calculate the end of the week (Friday) for a given date.
    
    The weekly reset happens on Saturday, so weeks run Saturday-Friday.
    
    Args:
        reference_date: A date or datetime to calculate the week end from
        
    Returns:
        The date of the Friday that ends the week containing reference_date
    """
    week_start = get_week_start(reference_date)
    return week_start + timedelta(days=6)
