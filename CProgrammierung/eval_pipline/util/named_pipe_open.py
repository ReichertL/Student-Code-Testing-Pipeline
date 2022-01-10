import os
import subprocess
 """
 Functions creating a named Pipe. Used to store output of subprocesses.
 Contains class NamedPipeOpen and NamedPipeCopy.
 """

class NamedPipeOpen(object):
    def __init__(self, path):
        """
        Parameters: 
            path (string): Path to file where the contents of the Pipe are placed.
        
        """
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        self.fifo_path = './stdin_pipe_' + os.path.basename(path)
        self.npc = NamedPipeCopy(path, self.fifo_path)
        self.npc.__enter__()
        self.f = open(self.fifo_path, 'br')

    def close(self):
        self.__exit__()

    def __enter__(self, *args):
        return self.f

    def __exit__(self, *args):
        self.f.close()
        self.npc.__exit__()


class NamedPipeCopy(object):
    """Create a named pipe "to" and write the content of "frm" to "to" using cat."""

    def __init__(self, frm, to):
        self.to = to
        self.frm = frm
        assert not os.path.exists(to)
        if os.path.exists(frm):
            os.mkfifo(to, mode=os.stat(frm).st_mode & 0o777)
            self.p = subprocess.Popen('cat {} > {}'.format(frm, to), shell=True)
        else:
            self.p = None

    def __enter__(self, *args):
        return self.to

    def __exit__(self, *args):
        if self.p is not None:
            self.p.kill()
            os.unlink(self.to)
