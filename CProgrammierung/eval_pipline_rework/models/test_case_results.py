class TestCaseResults:
    id: str = ''
    vg: dict
    ignore: list = []
    type_good_input: bool = True
    signal: int = 0
    segfault: bool = True
    timeout: bool = True
    cpu_time: float = None
    realtime: float = None
    tictoc: float = None
    mrss: int = -1
    return_code: int = -128
    output_correct: bool = False
    error_msg_quality: int = -1
    error_line: str = ''
