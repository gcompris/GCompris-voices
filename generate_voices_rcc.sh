#!/bin/bash
#
# generate_voices_rcc.sh
#
# Copyright (C) 2014 Holger Kaelberer
#
# Generates Qt binary resource files (.rcc) for voices locales.
#
# Usage:
# cd git/GCompris-voices/
# generate_voices_rcc.sh
#
# Results will be written to $PWD/.rcc/ which is supposed be synced to the
# upstream location.
#

QRC_DIR="."
RCC_DIR=".rcc"
#RCC_DEFAULT=`which rcc 2>/dev/null`   # default, better take /usr/bin/rcc?
RCC_DEFAULT=$Qt5_DIR/bin/rcc
CONTENTS_FILE=Contents
MD5SUM=/usr/bin/md5sum

[ -z "${RCC}" ] && RCC=${RCC_DEFAULT}

[ -z "${RCC}" ] && {
    echo "No rcc command in PATH, can't continue. Try to set specify RCC in environment:"
    echo "RCC=/path/to/qt/bin/rcc $0"
    exit 1
}

function generate_rcc {
    # Generate RCC 
    echo -n "$1 ... "
    ${RCC} -binary $1 -o $2

    echo "md5sum ... "
    cd ${RCC_DIR}
    ${MD5SUM} `basename $2` >>${CONTENTS_FILE}
    cd - &>/dev/null
}

echo "Generating binary resource files in ${RCC_DIR}/ folder:"

[ -d ${RCC_DIR} ] && rm -rf ${RCC_DIR}
mkdir  ${RCC_DIR}

#header of the global qrc (all the langs)
QRC_ALL_FILE="${QRC_DIR}/voices.qrc"
RCC_ALL_FILE="${RCC_DIR}/voices.rcc"
(cat <<EOHEADER
<!DOCTYPE RCC><RCC version="1.0">
<qresource>
EOHEADER
) > $QRC_ALL_FILE


for LANG in `find . -maxdepth 1 -regextype posix-egrep -type d -regex "\./[a-z]{2,3}(_[A-Z]{2,3})?"`; do
    QRC_FILE="${QRC_DIR}/voices-${LANG#./}.qrc"
    RCC_FILE="${RCC_DIR}/voices-${LANG#./}.rcc"

    # Generate QRC:
    echo -n "  ${LANG#./}: ${QRC_FILE} ... "
    # check for junk in the voices dirs:
    if [ ! -z "`git status --porcelain ${LANG} | grep '^??'`" ]; then
        echo "Found untracked files in your git checkout below ${LANG}. Better "git clean -f" it first!";
        exit 1;
    fi
    [ -e ${QRC_FILE} ] && rm ${QRC_FILE}

    #header:
    (cat <<EOHEADER
<!DOCTYPE RCC><RCC version="1.0">
<qresource>
EOHEADER
) >> $QRC_FILE
    for i in `find ${LANG} -not -type d`; do
	# For the lang file
        echo "    <file>${i#./}</file>" >> $QRC_FILE
	# For the all lang file
        echo "    <file>${i#./}</file>" >> $QRC_ALL_FILE
    done
    #footer:
    (cat <<EOFOOTER
</qresource>
</RCC>
EOFOOTER
) >> $QRC_FILE

    generate_rcc ${QRC_FILE} ${RCC_FILE} 

done

#footer of the global qrc (all the langs)
(cat <<EOFOOTER
</qresource>
</RCC>
EOFOOTER
) >> $QRC_ALL_FILE

generate_rcc ${QRC_ALL_FILE} ${RCC_ALL_FILE} 

cleanup:
rm -f *.qrc

echo "Finished! Now do something like:"
echo "rsync -avx ${RCC_DIR}/  www.gcompris.net:/path/to/www/gcompris/data/voices/"
#EOF
