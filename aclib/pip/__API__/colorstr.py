
def colorstr(color: int, *content):
    return f'\033[{color}m' + ' '.join(f'{content}' for content in content) + '\033[0m'

def redstr(*content):
    return colorstr(31, *content)

def greenstr(*content):
    return colorstr(32, *content)

def yellowstr(*content):
    return colorstr(33, *content)
