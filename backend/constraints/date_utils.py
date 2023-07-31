
from datetime import date,datetime

def convert_isodate(d:date|str):
    if isinstance(d,(date,datetime)):
        return d
    if isinstance(d,str):
        return date.fromisoformat(d)

def nth_of_month(week_no:int,target_weekday:int,month:int,year:int):
    match (week_no,target_weekday,month,year):
        case (int(),int(),int(),int()):
            pass
        case _:
            raise TypeError (f'nth of month takes four int arguments (got {(target_weekday,month,year)})')
    if target_weekday<0 or target_weekday>6:
        raise ValueError(f'Weekday must be between 0 and 6 (got "{target_weekday}")')
    if month<1 or month>12:
        raise ValueError(f'Month must be between 1 and 12 (got "{month}")')
    first_of_month=date(year,month,1)
    first_weekday=first_of_month.weekday()
    if first_weekday>target_weekday:
        offset=target_weekday-first_weekday
    else:
        offset=target_weekday-first_weekday-7
    target_day=(week_no*7)+offset+1
    return date(year,month,target_day)

def is_nth_of_month(date1:date,date2:date):
    if not (isinstance(date1,date) and isinstance(date2,date)):
        raise TypeError('expected two dates')
    if date1.weekday()!=date2.weekday():
        return False
    if date1.day//7 == date2.day//7:
        return True
    return False

def is_cycle(date1:date,date2:date,cycle_length):
    if date1.weekday()!=date2.weekday():
        return False
    return ((date2-date1).days)%(cycle_length*7)==0

if __name__=='__main__':
    weekdays='Monday Tuesday Wednesday Thursday Friday Saturday Sunday'.split()
    ordinals='0th 1st 2nd 3rd 4th 5th'.split()
    print(f'First day in July 2023 is {weekdays[date(2023,7,1).weekday()]}')
    for wkno in range(1,2):
      for wkday in range(7):
        print(f'{ordinals[wkno]} {weekdays[wkday]} in July 2023 is {nth_of_month(wkno,wkday,7,2023)}')
    print(nth_of_month(2,2,7,2023),nth_of_month(2,2,8,2023))
    print(is_nth_of_month(nth_of_month(2,2,7,2023),nth_of_month(2,2,8,2023)))
    print(is_cycle(date(2023,8,8),date(2023,8,1),1))

    