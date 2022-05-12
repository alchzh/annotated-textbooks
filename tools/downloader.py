import urllib3
from hashlib import md5
from io import BytesIO
from typing import Optional, BinaryIO
from shutil import copyfileobj, COPY_BUFSIZE

GATEWAYS = [
    "https://{cidv1b32}.ipfs.cf-ipfs.com/",
    "https://{cidv1b32}.ipfs.dweb.link/"
]

def get_ipfs_url(cid: str, path: Optional[str] = None, request_opts: dict = {}) -> str:
    http = urllib3.PoolManager()

    errors = []
    for gateway in GATEWAYS:
        url = gateway.format(cidv1b32=cid)
        if path:
            url += path

        try:
            r = http.request("HEAD", url, **request_opts)
            if r.status != 200:
                raise urllib3.exceptions.RequestError(f"Got status code {r.status}")
            return r.geturl()
        except urllib3.exceptions.RequestError as e:
            errors.append(e)
    raise Exception([errors])

class ChecksumError(Exception):
    pass

def copyfileobj_md5(fsrc: BinaryIO, fdst: BinaryIO, md5sum: str, length: int = 0):
    if not length:
        length = COPY_BUFSIZE

    fsrc_read = fsrc.read
    fdst_write = fdst.write
    m = md5()
    u = m.update
    while True:
        buf = fsrc_read(length)
        if not buf:
            break
        u(buf)
        fdst_write(buf)

    hd = m.hexdigest().upper()
    if hd != md5sum.upper():
        raise ChecksumError(f"Downloaded md5sum {hd} does not match {md5sum}")

def download(url: str, md5sum: Optional[str] = None, save: Optional[str] = None, request_opts: dict = {}) -> Optional[BinaryIO]:
    http = urllib3.PoolManager()

    r = http.request("GET", url, preload_content=False, **request_opts)
    if md5sum and save is None:
        f = BytesIO()
        copyfileobj_md5(r, f, md5sum)
        f.seek(0)
        return f
    elif save is not None:
        with open(save, "wb") as f:
            if md5sum:
                copyfileobj_md5(r, f, md5sum)
            else:
                copyfileobj(r, f)
