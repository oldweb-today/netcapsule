#!/bin/bash

sudo chown browser:browser /download
cd /download

wget http://ftp.netscape.com/pub/communicator/english/4.79/unix/supported/linux22/navigator_standalone/navigator-v479-us.x86-unknown-linux2.2.tar.gz

tar xvfz navigator-v479-us.x86-unknown-linux2.2.tar.gz

cd ./navigator-v479.x86-unknown-linux2.2
sudo ./ns-install

cd /download
wget http://archive.debian.org/debian/pool/main/e/egcs1.1/libstdc++2.9-glibc2.1_2.91.66-4_i386.deb
wget http://archive.debian.org/debian/pool/main/g/glibc/libc6_2.2.5-11.8_i386.deb
wget http://archive.debian.org/debian/pool/main/x/xfree86/xlibs_4.1.0-16woody6_i386.deb

mkdir /tmp/oldlibs

dpkg -x /download/libstdc++2.9-glibc2.1_2.91.66-4_i386.deb /tmp/oldlibs
dpkg -x /download/libc6_2.2.5-11.8_i386.deb /tmp/oldlibs
dpkg -x /download/xlibs_4.1.0-16woody6_i386.deb /tmp/oldlibs

NETSCAPE_LIB=/opt/netscape/lib
sudo mkdir $NETSCAPE_LIB

sudo cp /tmp/oldlibs/usr/X11R6/lib/*.so.* $NETSCAPE_LIB
sudo cp /tmp/oldlibs/usr/lib/*.so.* $NETSCAPE_LIB
sudo cp /tmp/oldlibs/lib/*.so.* $NETSCAPE_LIB

sudo mkdir -p /usr/X11R6/lib/X11
sudo ln -s /usr/share/X11/locale /usr/X11R6/lib/X11/

NETSCAPE_USER=/home/browser/.netscape

mkdir $NETSCAPE_USER

sudo chown browser:browser $NETSCAPE_USER
chmod 700 $NETSCAPE_USER

cd $NETSCAPE_USER

mkdir ./archive
mkdir ./cache

chmod 700 ./archive
chmod 700 ./cache

