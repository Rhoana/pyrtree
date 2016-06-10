
def take(n,f,*args,**kwargs):
    i = 0
    while i < n:
        yield f(*args,**kwargs)
        i = i + 1
