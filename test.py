
tst='== 1'

match tst.partition(' '):
    case ('==',' ',d) if int(d):
        print(d)
    case _:
        print('nah')