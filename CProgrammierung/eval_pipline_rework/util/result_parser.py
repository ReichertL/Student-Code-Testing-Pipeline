import re
import logging

from alchemy.valgrind_outputs import Valgrind_Output

FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)

re_pid = re.compile(rb'==\d+==')
re_error = re.compile(rb'(?i)error|warn|unknown|not|wrong|invalid|fehler|unbekannt|kein|nicht|falsch')
re_letter = re.compile(rb'[a-zA-Z]')

re_vg_heap_summary1 = re.compile(rb'\s*in use at exit: ([0-9,]+) bytes in ([0-9,]+) blocks')
re_vg_heap_summary2 = re.compile(rb'\s*total heap usage: ([0-9,]+) allocs, ([0-9,]+) frees, ([0-9,]+) bytes allocated')
re_vg_pass = re.compile(rb'\s*All heap blocks were freed -- no leaks are possible')
re_vg_outofmemory = re.compile(rb"\s*Valgrind's memory management: out of memory:")
re_vg_error_summary = re.compile(
    rb'\s*ERROR SUMMARY: ([0-9,]+) errors from ([0-9,]+) contexts \(suppressed: ([0-9,]+) from ([0-9,]+)\)')
re_vg_leak_details = re.compile(rb'\s*?([a-z][a-z ]*): ([0-9,]+) bytes in ([0-9,]+) blocks')
re_vg_invalid_write = re.compile(rb'\s*Invalid write of size')
re_vg_invalid_read = re.compile(rb'\s*Invalid read of size')

re_time_signal = re.compile(r"Command terminated by signal (\d+)")


class ResultParser:
    @staticmethod
    def parse_time_file(testcase_result, file):
        for line in file:
            mo = re_time_signal.match(line)
            if mo is not None:
                signal = int(mo.group(1))
                testcase_result.signal = signal
                if signal == 9:
                    testcase_result.timeout = True
                elif signal == 11:
                    testcase_result.segfault = True
                continue
            if line.startswith('Command'):
                continue
            ls = line.split()
            testcase_result.cpu_time = float(ls[0]) + float(ls[1])
            testcase_result.mrss = 1024 * int(ls[2])
            testcase_result.return_code = int(ls[3])
            realtime = float(ls[4])
            break

    @staticmethod
    def parse_valgrind_file(testcase_id,lines):
        res=Valgrind_Output(testcase_id)
        lines = list(lines)
        it = iter(lines)
        valgrind_head = re_pid.match(next(it)).group()
        while True:
            try:
                line = next(it)
            except StopIteration:
                break
            if not line.startswith(valgrind_head):
                continue
            line = line[len(valgrind_head) + 1:]
            if re_vg_pass.match(line) is not None:
                res.ok= True
                continue
            if re_vg_outofmemory.match(line) is not None:
                res.ok = None
                continue
            if line == b'HEAP SUMMARY:\n':
              #  res.in_use_at_exit = parse_int_tuple(                  #TODO
                   # re_vg_heap_summary1.match(next(it)[len(valgrind_head) + 1:]).groups())
              #  res.total_heap_usage = parse_int_tuple(
                   # re_vg_heap_summary2.match(next(it)[len(valgrind_head) + 1:]).groups()) #TODO
                continue
            if line == b'LEAK SUMMARY:\n':
                d = {}
                for key in ('definitely lost', 'indirectly lost', 'possibly lost',
                            'still reachable', 'suppressed'):
                    mo = re_vg_leak_details.match(next(it)[len(valgrind_head) + 1:])
                    assert key == mo.group(1).decode('ascii')
                    d[key] = parse_int_tuple(mo.groups()[1:])
                #res['leak_summary'] = d #TODO
                continue
            mo = re_vg_error_summary.match(line)
            if mo is not None:
                #res['error_summary'] = parse_int_tuple(mo.groups()) # TODO
                continue
            mo = re_vg_invalid_read.match(line)
            if mo is not None:
                res.invalid_read_count += 1
                continue
            mo = re_vg_invalid_write.match(line)
            if mo is not None:
                res.invalid_write_count += 1
                continue
        return res

    @staticmethod
    def parse_error_file(testcase_result):
        testcase_result.error_msg_quality = 0
        for discriptor, file_path in [('stderr', 'test.stderr'), ('stdout', 'test.stdout')]:
            with open(file_path, 'br') as file:
                for line in file:
                    if testcase_result.error_msg_quality == 0:
                        mo = re_letter.search(line)
                        if mo is not None:
                            testcase_result.error_msg_quality = 1
                            testcase_result.error_line = discriptor + ": " + line.decode('ascii', 'ignore')
                            testcase_result.error_line = testcase_result.error_line.strip()
                    mo = re_error.search(line)
                    if mo is not None:
                        testcase_result.error_msg_quality = 2
                        testcase_result.error_line = discriptor + ": " + line.decode('ascii', 'ignore')
                        testcase_result.error_line = testcase_result.error_line.strip()
                        break
                if testcase_result.error_msg_quality == 2:
                    break


def commabytes2int(b):
    return int(b.decode('ascii').replace(',', ''))


def parse_int_tuple(bytes_tuple):
    return tuple(map(commabytes2int, bytes_tuple))
