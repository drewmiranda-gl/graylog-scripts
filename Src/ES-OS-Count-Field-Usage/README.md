# How to "install"

This is done via the terminal.

1. Download/copy files locally
    * `es-os-count-field-usage.py` (the main script)
    * `pyenv-init.sh` (automate setting up pyvenv and installing requirements)
    * `requirements.txt` (used by above to install dependencies)
    * `launch.sh` (helper to launch main script using pyvenv)
2. Execute `pyenv-init.sh`
    * e.g.
        * `chmod +x *.sh`
        * `./pyenv-init.sh`
3. Run script, see examples below
    * `./launch.sh es-os-count-field-usage.py`

# Examples

NOTE: this script is somewhat slow and may take a long while to run depending on how many indices and fields you have.

## No Authentication

```sh
./launch.sh es-os-count-field-usage.py --api-url http://hostname.domain.tld:9200/
```

## HTTP Basic Authentication (Username/Password)

```sh
./launch.sh es-os-count-field-usage.py --api-url http://hostname.domain.tld:9200/ --username iamuser --password supersecret
```

## Client Certificate Authentication (cert and key files)

For example, when using Graylog Data Node:

```sh
./launch.sh es-os-count-field-usage.py --api-url https://hostname.domain.tld:9200/ --cert cert.crt --key cert.key --no-verify
```

# What does this do?

1. Get a list of all Indices using `/_cat/indices?h=health,status,index,docs.count`
2. For each index, get a list of field names
3. For each field name of each index, count how many times the field is used in the index, using  `/<index>/_count/`
4. Outputs in console in CSV format. Pipe output to a file, for example `> out.csv` to open in another tool, such as Microsoft Excel