import subprocess


def parse_lineoutput(data):
    chunks = data.split('\n\n')
    return [
        dict(x.strip().split(' = ')
             for x in chunk.splitlines())
        for chunk in chunks if chunk.strip()
    ]


def output_or_raise(*args):
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        universal_newlines=True,
    )
    out, ignored = proc.communicate()
    if proc.returncode:
        raise Exception(proc.returncode, out, ignored)
    return out
