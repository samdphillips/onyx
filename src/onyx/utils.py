
def camel_to_snake(name):
    s = name[0].lower()
    for c in name[1:]:
        if c.isupper():
            s += "_" + c.lower()
        elif c == ':':
            s += "_"
        else:
            s += c
    return s
