def smart_open(filename, mode = 'rt'):
    if filename.endswith('.gz'):
        return gzip.open(filename, mode=mode, encoding='utf-8')
    else:
        return open(filename, mode=mode, encoding='utf-8')
