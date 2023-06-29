
from collections import deque


def expand(template,head=None):
    if head is None:
        head=[]
    tmp=deque(template)
    while tmp:
        a,b,c =tmp.popleft()
        if isinstance(a,tuple):
            for x in a:
                yield from expand([(x,b,c),*tmp],head[:])
            return
        else:
            head.append((a,b,c))
    yield head

for e in expand([(1,2,3),((4,5),6,7),((7,8),9,10)]):
    print (e)