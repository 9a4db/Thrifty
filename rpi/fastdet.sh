#!/bin/bash

set -e

echo "Waiting for NTP sync"
ntp-wait

echo "Starting fastdet"
cd /home/pi/detector
TOAD_FILE="toad/$(date +"%Y-%m-%d_%H-%M-%S").toad"
CARD_FILE="card/$(date +"%Y-%m-%d_%H-%M-%S").card"
. ./fastdet.cfg
CARD_ARG=
if [ -n "${EXPORT_CARD}" ]; then
    CARD_ARG="-x ${CARD_FILE}"
fi
exec fastdet \
    -r ${RXID} \
    -t ${THRESH_CARRIER} \
    -u ${THRESH_CORR} \
    -k ${SKIP} \
    -w ${WINDOW} \
    -m ${WISDOM_FILE} \
    -z ${TEMPLATE_FILE} \
    -i rtlsdr \
    -f ${RTL_FREQ} \
    -g ${RTL_GAIN} \
    -o ${TOAD_FILE} ${CARD_ARG} >>capture.log
