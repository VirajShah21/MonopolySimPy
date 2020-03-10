def merge(*args):
    out = []

    for ls in args:
        for item in ls:
            out.append(item)

    return out
