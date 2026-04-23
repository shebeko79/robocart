#!/bin/sh

IFACE="$1"
EVENT="$2"

if [ "$EVENT" = "CONNECTED" ]; then
    echo "WiFi connected, restarting DHCP"

	if [ -e /run/udhcpc.wlan0.pid ]
	then
		kill `cat /run/udhcpc.wlan0.pid` || true
		rm -f /run/udhcpc.wlan0.pid
	fi
    udhcpc -i "$IFACE" -t 10 -T 1 -A 5 -b -p /run/udhcpc.wlan0.pid
fi
