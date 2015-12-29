class TooManyDumpFiles(Exception):
    def __init__(self):
        Exception.__init__(self, 'TOO_MANY_DUMP_FILES')
