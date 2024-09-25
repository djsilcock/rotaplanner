import contextlib

@contextlib.contextmanager
def passthrough(val):
    yield val

a=[]

with passthrough(6) as a:
    print (a)
    with passthrough(7) as a:
        print (a)
    print (a)