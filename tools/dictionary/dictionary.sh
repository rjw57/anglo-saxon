#!/bin/sh

(sleep 1; xdg-open http://localhost:8000/) &
cd `dirname $0`
python -m http.server

