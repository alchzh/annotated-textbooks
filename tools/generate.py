from typing import Optional, TypedDict, Dict, Iterable
from pathlib import Path
import subprocess
from shutil import copyfileobj

from util import cd
from downloader import get_ipfs_url, download

from pikepdf import (
    Pdf,
    Array,
    Dictionary,
    Name
)

class AnnotateConfig(TypedDict):
    ipfs_cid: str
    source_md5sum: str
    filename: str

    labels: Dict[str, "LabelConfig"]

class LabelConfig(TypedDict):
    startpage: int
    prefix: str
    style: Optional[str]
    firstpagenum: int


def _style_Name(style: str):
    if not style:
        return None
    else:
        return Name("/" + style)

def make_PdfPageLabels(labels: Iterable[LabelConfig]):
    return Dictionary(
        Nums=Array(
            el for label in labels for el in (
                label["startpage"],
                Dictionary(
                    S=_style_Name(label["style"]),
                    St=label["firstpagenum"],
                    P=label["prefix"]
                )
            )
        )
    )

def get_pdf(config: AnnotateConfig, directory_path: str) -> Pdf:
    with cd(directory_path):
        dl_dir = Path("original")
        dl_dir.mkdir(exist_ok=True)

        dl_path = dl_dir / config["filename"]

        if dl_path.exists():
            f = open(dl_path, "rb")
        else:
            f = download(get_ipfs_url(config["ipfs_cid"]), md5sum=config["source_md5sum"])
            with open(dl_path, "wb") as out:
                copyfileobj(f, out)
            f.seek(0)

        p = Pdf.open(f)
        return p

def add_PageLabels(p: Pdf, config: AnnotateConfig):
    p.Root.PageLabels = p.make_indirect(
        make_PdfPageLabels(config["labels"].values())
    )

    print(p.pages[626].label)

if __name__ == "__main__":
    import json
    import sys

    config_path = Path(sys.argv[1])
    with open(config_path, "r") as f:
        config = json.load(f)
        p = get_pdf(config, config_path.parent)
        add_PageLabels(p, config)
        p.save(config_path.parent / config["filename"])
