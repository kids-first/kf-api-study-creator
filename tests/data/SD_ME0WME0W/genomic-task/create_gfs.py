#############################################################
# Generate genomic-files. These will be uploaded by hand to
# the appropriate S3 buckets.
#############################################################

import os
import random as ra
import string


DATA_DIR = "sample_gfs"
HARM_DIR = os.path.join(DATA_DIR, "harmonized")
UNHARM_DIR = os.path.join(DATA_DIR, "unharmonized")


def create(n=10):
    """
    Create n separate and distinct unharmonized genomic files.
    In order to better simulate
    actual studies, each will have 3 versions with different extensions,
    including .crai, .cram, and .md5. Each of these 3n files will simply be
    a text file with a randomly-generated string of text. These files will
    then need to be manually uploaded to their respective S3 buckets.

    Also create n harmonized genomic files. I'm not exactly sure how the
    file formats work here. For each .cram file, add .gz at the end.
    """

    if not os.path.isdir(DATA_DIR):
        os.mkdir(DATA_DIR)
    if not os.path.isdir(UNHARM_DIR):
        os.mkdir(UNHARM_DIR)
    if not os.path.isdir(HARM_DIR):
        os.mkdir(HARM_DIR)


    for extension in {".cram", ".cram.crai", ".cram.md5"}:
        for i in range(n):
            make_file(i, extension)
            # Only create a harmonized counterpart to the .cram files
            # (crai and md5 are index files)
            if extension == ".cram":
                make_file(i, ".cram.gz", harmonized=True)


def make_file(i, extension, harmonized=False):
    # Generate random text of random length
    file_text = "".join(
        ra.choice(string.ascii_letters + string.digits) for _ in range(
            ra.randint(10, 1000)
        )
    )
    BASE_DIR = HARM_DIR if harmonized else UNHARM_DIR
    filename = os.path.join(
        BASE_DIR, f"genomic-file-{i}{extension}"
    )
    with open(filename, "w") as f:
        f.write(file_text)


if __name__ == "__main__":
    # For testing we should probably make these files the same each time
    ra.seed(0)
    create()






