"""constraint manager"""


from collections import deque



def get_constraint_atom(generic_context, key):
    """Boolean atom for enforcement"""
    name = ('constraint', key)
    enforce_this = generic_context.dutystore[name]
    generic_context.constraint_atoms.append(enforce_this)
    return enforce_this

def sliding_date_range(days,length):
    "returns window of dates.Pre-filters are passed to underlying days iterator"
    date_deque = deque(maxlen=length)
    for day in days:
        date_deque.append(day)
        if len(date_deque) == length:
            yield date_deque
