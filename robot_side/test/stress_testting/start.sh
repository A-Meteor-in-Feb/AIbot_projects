#!/bin/bash
#wg-quick up wg0

exec python mqtt_stressTesting.py "$@"
