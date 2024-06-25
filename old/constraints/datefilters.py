"Various filters for self.days() iterator"

from datetime import date

def exclusion(start, end):
    "exclude the given date range"
    def f(d:date):
        if d >= start and d <= end:
            return False
        return True
    return f

def inclusion(start,end):
    "only include the given date range - inverse of exclusion()"
    exc_func=exclusion(start,end)
    def f(d:date):
        return not exc_func(d)
    return f

def include_weekdays(*weekdays:int):
    "only include the given weekdays"
    def f(d:date):
        return d.weekday() in weekdays
    return f


