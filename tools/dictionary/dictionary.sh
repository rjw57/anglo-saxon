#!/bin/sh

cd `dirname $0`

case `uname` in
  Darwin)
    (sleep 1; open http://localhost:8000/) &
    python -m SimpleHTTPServer
    ;;
  *)
    (sleep 1; xdg-open http://localhost:8000/) &
    if [ -z `which python3` ]; then
      python -m SimpleHTTPServer
    else
      python3 -m http.server
    fi
    ;;
esac

