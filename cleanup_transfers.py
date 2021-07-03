import glob
import subprocess
import time
import os

print("Starting transfer program...")
chunk_size_limit = 500
file_list = []
tmp = '/tmp/transfer'


def get_files():
    return glob.glob('/home/pi/*.jpg')


while True:  # Daemon
    file_list = get_files()
    num_files = len(file_list)

    # if there are any files
    if num_files > 0:

        # wait while we are accumulating files, unless we reach a critical mass
        while len(get_files()) > num_files and num_files <= chunk_size_limit:
            file_list = get_files()
            num_files = len(file_list)
            time.sleep(2)

        if num_files > chunk_size_limit:
            print(f"Reached chunk_size_limit of {chunk_size_limit}!")

        print(f"{num_files} file(s) to transfer...")

        # create temp dir if not exist
        if not os.path.exists(tmp):
            os.mkdir(tmp)

        # sort files in-place
        file_list.sort()

        # move all files to temp dir
        for file in file_list:
            os.rename(file, f'{tmp}/{file.split("/")[-1]}')

        try:
            # attempt to bulk scp them
            transfer = subprocess.run(
                f'scp {tmp}/* barney@dinkleberg.local:/home/barney/projects/MotionEvents/',
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                shell=True,
                text=True
            )

            # if successfully transferred
            if transfer.returncode == 0:
                print(transfer.stdout)
                print(f"Successfully transferred files, now attempting deletion...")

                try:
                    # now attempt to bulk delete
                    delete = subprocess.run(
                        f'rm -f {tmp}/*',
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        shell=True,
                        text=True
                    )

                    # if success
                    if delete.returncode == 0:
                        print(delete.stdout)
                        print(f"Successfully deleted files.")
                    else:
                        print(delete.stderr)
                        print(f"Unable to delete, return_code = {delete}")
                except Exception as re:
                    print(f"ERROR deleting: {type(re).__name__}")
            else:
                print(transfer.stderr)
                print(f"Unable to transfer, return_code = {transfer}")
        except Exception as e:
            print(f"ERROR transferring: {type(e).__name__}")

        print(f"Finished with batch.")

    time.sleep(5)
