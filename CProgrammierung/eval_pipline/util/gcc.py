"""
This module provides functions to compile a single c file using gcc.

The host's native gcc can be used as less as a gcc inside a docker container.
"""
import os
import shutil
import logging
from pwd import getpwnam
from subprocess import run, DEVNULL, PIPE
import sys
import shutil

OWN_PW = getpwnam(os.environ['USER'])
OWN_UID_GID = f'{OWN_PW.pw_uid:d}.{OWN_PW.pw_gid:d}'
SUDO_DOCKER = ['sudo', 'docker']


FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.warning)

class DockerError(RuntimeError):
    pass


def native_gcc(gcc_args, src, dest):
    """Call gcc to compile C file `src` procuding executable `dest`

    arguments:

    gcc_args : str
      all gcc args up to `src -o dest`

    src : str
      path of c file

    dest : str
      path of executable

    RETURNS:

    A tuple

    (commandline : str, return_code : int, gcc_stderr : str)
    """

    directory = os.path.dirname(dest)
    tmp_c_path = dest + '.c'
    shutil.copy(src, tmp_c_path)
    all_args = gcc_args + ['-o', os.path.basename(dest),
                           os.path.basename(dest) + '.c']
    cp = run(all_args,
             stdout=DEVNULL,
             stderr=PIPE,
             universal_newlines=True,
             errors='ignore',
             cwd=directory, check=False)
    os.unlink(tmp_c_path)
    #logging.info('native_gcc "{}" -> {}'.format(src, cp.returncode))
    return ' '.join(all_args), cp.returncode, cp.stderr


def docker_gcc(gcc_args, src, dest, docker_image, docker_container, directory):
    """Call gcc to compile C file `src` procuding executable `dest`

    - This function uses the gcc found in the given docker image/container.
    - If `directory` exists, it must be empty
        (this is required to avoid overwriting any files)
    - The container is created and started as needed.
    - The docker image must include a bash as well as a gcc installed at the
      configured path.

    Apart from the additional docker specific arguments, this function's
    interface is identical to `native_gcc`.

    arguments:

    gcc_args : str
      all gcc args up to `src -o dest`

    src : str
      path of c file

    dest : str
      path of executable

    RETURNS:

    A tuple

    (commandline : str, return_code : int, gcc_stderr : str)
    """
    # create shared directory, if it does not exist already:

    try:
         os.remove(dest)
    except:
        pass
    
    try:
        os.mkdir(directory)
    except:
        pass
    
    if os.listdir(directory):
        files=os.path(directory)
        for file in files:
            os.remove(file)
        logger.error(f"Directory not empty: '{directory}'")
        #raise OSError(f"Directory not empty: '{directory}'")
    
    # create docker container, if it does not exist already
    run(SUDO_DOCKER + ['create',
                       '--name', docker_container,
                       '-v', f'{os.path.abspath(directory)}:/host',
                       docker_image],
        stdout=DEVNULL,
        stderr=DEVNULL)
   
    # start docker container if required#
    cp = run(SUDO_DOCKER + ['start', docker_container], stdout=DEVNULL, stderr=sys.stderr)
    if cp.returncode != 0:
        logging.info(cp)
        raise DockerError(f'Unable to start docker container {docker_container} based on docker image {docker_image}.')
    # copy c file
    tmp_c_basename = os.path.basename(dest) + '.c'
    tmp_c_path = os.path.join(directory, tmp_c_basename)
    shutil.copy(src, tmp_c_path)
    # execute gcc in docker container
    all_args = gcc_args + ['-o', os.path.basename(dest),
                           os.path.basename(dest) + '.c']
    commandline = ' '.join(all_args)
    
    command_full= SUDO_DOCKER + ['exec',
         '-w', '/host',
         docker_container,
         'bash', '-c',
         f'{commandline} 2> gcc.stderr ; '
         'echo $? > gcc.return ;'
         f'chown {OWN_UID_GID} gcc.stderr gcc.return {os.path.basename(dest)}']
    #logging.debug(command_full)
    cp=run(command_full,
        stdout=DEVNULL,
        stderr=DEVNULL)
    # collect gcc's stderr
    with open(os.path.join(directory, 'gcc.stderr')) as f:
        gcc_stderr = f.read()
    os.unlink(os.path.join(directory, 'gcc.stderr'))
    # collect gcc's returncode
    with open(os.path.join(directory, 'gcc.return')) as f:
        gcc_returncode = int(next(f))
    os.unlink(os.path.join(directory, 'gcc.return'))
    # try to move the executable produced by gcc to `dest`
    if gcc_returncode == 0:
        try:
            shutil.move(os.path.join(directory, os.path.basename(dest)), dest)
        except FileNotFoundError:
            pass
    # clean up copy of c file
    os.unlink(tmp_c_path)
    # directory should now be back in its original state, most likely empty
    #logging.info('docker_gcc "{}" -> {}'.format(src, gcc_returncode))
    
    #cp = run(SUDO_DOCKER + ['stop', docker_container],stdout=sys.stdout, stderr=sys.stderr)
    #if cp.returncode!=0:
    #   	logging.error(cp)
    #    logging.error(f'Unable to stop docker container {docker_container} based on docker image {docker_image}.')
    return commandline, gcc_returncode, gcc_stderr

def hybrid_gcc(gcc_args, src, dest, docker_image, docker_container, directory):
    #print(gcc_args)
    commandline, gcc_returncode, gcc_stderr = docker_gcc(
        gcc_args, src, dest, docker_image, docker_container, directory)
    if gcc_returncode == 0:
        native_args = gcc_args.copy()
        try:
            native_args.remove('-Werror')
        except ValueError:
            pass
        native_gcc(native_args, src, dest)
    return commandline, gcc_returncode, gcc_stderr
