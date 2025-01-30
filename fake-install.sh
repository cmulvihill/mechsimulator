# run with: . /path/to/fake-install.sh
export _THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

for d in ls $_THIS_DIR/*/*; do
    export PATH=$d:$PATH
    export PYTHONPATH=$d:$PYTHONPATH
done

for d in ls $_THIS_DIR/*/; do
    export PATH=$d:$PATH
    export PYTHONPATH=$d:$PYTHONPATH
done

