#!/bin/sh

# The following code is taken directly from
# http://blog.scphillips.com/posts/2013/07/getting-a-python-script-to-run-in-the-background-as-a-service-on-boot/
# Thanks to Stephen Christopher Phillips for posting
# To use the scripts follow the instructions at the above link, but essentially
# 1. Copy the init script into /etc/init.d, using: sudo cp weatherProcessor.sh /etc/init.d
# 2. Ensure the init script is executable, using: sudo chmod 755 /etc/init.d/weatherProcessor.sh
# To start the python script use: sudo /etc/init.d/weatherProcessor.sh start
# To check the status use: /etc/init.d/weatherProcessor.sh status
# To stop the script use: sudo /etc/init.d/weatherProcessor.sh stop
# To get the script to start at startup use: sudo update-rc.d weatherProcessor.sh defaults




### BEGIN INIT INFO
# Provides:          weatherProcessor
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Put a short description of the service here
# Description:       Put a long description of the service here
### END INIT INFO

# Change the next 3 lines to suit where you install your script and what you want to call it
DIR=/home/pi/WhatsUpWithTheWeather
DAEMON=$DIR/weatherProcessor.py
DAEMON_NAME=weatherProcessor

# Add any command line options for your daemon here
DAEMON_OPTS=""

# This next line determines what user the script runs as.
# Root generally not recommended but necessary if you are using the Raspberry Pi GPIO from Python.
DAEMON_USER=pi

# The process ID of the script when it runs is stored here:
PIDFILE=/var/run/$DAEMON_NAME.pid

. /lib/lsb/init-functions

do_start () {
    log_daemon_msg "Starting system $DAEMON_NAME daemon"
    start-stop-daemon --start --background --pidfile $PIDFILE --make-pidfile --user $DAEMON_USER --chuid $DAEMON_USER --startas $DAEMON -- $DAEMON_OPTS
    log_end_msg $?
}
do_stop () {
    log_daemon_msg "Stopping system $DAEMON_NAME daemon"
    start-stop-daemon --stop --pidfile $PIDFILE --retry 10
    log_end_msg $?
}

case "$1" in

    start|stop)
        do_${1}
        ;;

    restart|reload|force-reload)
        do_stop
        do_start
        ;;

    status)
        status_of_proc "$DAEMON_NAME" "$DAEMON" && exit 0 || exit $?
        ;;

    *)
        echo "Usage: /etc/init.d/$DAEMON_NAME {start|stop|restart|status}"
        exit 1
        ;;

esac
exit 0
