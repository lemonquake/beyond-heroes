"""Asset registry: @asset('name', 'category', col=True) registers a builder fn(kit) -> optional dict of finish options."""
REG = {}
ORDER = []


def asset(name, cat, col=True, fragments=False):
    def deco(fn):
        REG[name] = dict(fn=fn, cat=cat, col=col, fragments=fragments)
        ORDER.append(name)
        return fn
    return deco
