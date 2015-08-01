#!/bin/bash
#
# generate_voices_rcc.sh
#
# Copyright (C) 2014 Holger Kaelberer
#
# Generates Qt binary resource files (.rcc) for voices locales.
#
# Results will be written to $PWD/.rcc/ which is supposed be synced to the
# upstream location.
#

[ $# -ne 2 ] && {
    echo "Usage: generate_voices_rcc.sh ogg|aac|ac3|mp3 <path to gtk lang words dir>"
    exit 1
}
# Compressed Audio Format
CA=$1

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

WORDS_DIR=$2
[ ! -d "${WORDS_DIR}" ] && {
    echo "Words dir ${WORDS_DIR} not found"
    exit 1
}
[ -d words ] && rm -rf words
ln -s ${WORDS_DIR} words

function generate_rcc {
    # Generate RCC 
    echo -n "$2 ... "
    mkdir -p ${2%/*}
    ${RCC} -binary $1 -o $2

    echo "md5sum ... "
    cd ${2%/*}
    ${MD5SUM}  ${2##*/}>> ${CONTENTS_FILE}
    cd - &>/dev/null
}

function header_rcc {
(cat <<EOHEADER
<!DOCTYPE RCC><RCC version="1.0">
<qresource prefix="/gcompris/data">
EOHEADER
) > $1
}

function footer_rcc {
(cat <<EOFOOTER
</qresource>
</RCC>
EOFOOTER
) >> $1
}

echo "Generating binary resource files in ${RCC_DIR}/ folder:"

[ -d ${RCC_DIR} ] && rm -rf ${RCC_DIR}
mkdir  ${RCC_DIR}

#header of the global qrc (all the langs)
QRC_FULL_FILE="${QRC_DIR}/full-${CA}.qrc"
RCC_FULL_FILE="${RCC_DIR}/full-${CA}.rcc"
header_rcc $QRC_FULL_FILE

# Create the voices directory that will contains links to locales dir
VOICE_DIR="voices-${CA}"
[ -d ${RCC_DIR} ] && rm -rf ${RCC_DIR}
rm -rf ${VOICE_DIR}
mkdir -p ${VOICE_DIR}

for LANG in `find . -maxdepth 1 -regextype posix-egrep -type d -regex "\./[a-z]{2,3}(_[A-Z]{2,3})?" | sort`; do
    QRC_FILE="${QRC_DIR}/voices-${LANG#./}.qrc"
    RCC_FILE="${RCC_DIR}/${VOICE_DIR}/voices-${LANG#./}.rcc"

    # Populate the voices backlinks
    ln -s -t ${VOICE_DIR} ../$LANG

    # Generate QRC:
    echo -n "  ${LANG#./}: ${QRC_FILE} ... "
    # check for junk in the voices dirs:
    if [[ -d .git && ! -z "`git status --porcelain ${LANG} | grep '^??'`" ]]; then
        echo "Warning, found untracked files in your git checkout below ${LANG}. Better "git clean -f" it first!";
    fi
    [ -e ${QRC_FILE} ] && rm ${QRC_FILE}

    header_rcc $QRC_FILE
    for i in `find ${LANG} -not -type d | sort`; do
	# For the lang file
        echo "    <file>${VOICE_DIR}/${i#./}</file>" >> $QRC_FILE
	# For the all lang file
        echo "    <file>${VOICE_DIR}/${i#./}</file>" >> $QRC_FULL_FILE
    done
    footer_rcc $QRC_FILE
    generate_rcc ${QRC_FILE} ${RCC_FILE}

done

# Word images for the full qrc
for i in `find words/ -not -type d | sort`; do
    echo "    <file>${i#${WORDS_DIR}}</file>" >> $QRC_FULL_FILE
done

#footer of the global qrc (all the langs)
footer_rcc $QRC_FULL_FILE

echo -n "  full: ${QRC_FULL_FILE} ... "
generate_rcc ${QRC_FULL_FILE} ${RCC_FULL_FILE}

# Word images standalone rcc
# This is generated only when the script is called to generate ogg files
# as this is our reference and images does not depends on the audio codec
if [[ $CA == ogg ]]
then
    header_rcc "${QRC_DIR}/words.qrc"
    for i in `find words/ -not -type d | sort`; do
	echo "    <file>${i#${WORDS_DIR}}</file>" >> "${QRC_DIR}/words.qrc"
    done
    footer_rcc "${QRC_DIR}/words.qrc"
    echo -n "  words: "${QRC_DIR}/words.qrc" ... "
    generate_rcc "${QRC_DIR}/words.qrc" "${RCC_DIR}/words/words.rcc"
fi

#cleanup:
#rm -f *.qrc
#rm words
#rm -rf ${VOICE_DIR}

echo "Finished!"
echo ""
echo "Consolidate .rcc/Contents in a master ${RCC_DIR}"
echo "containing all the encoded content."
echo ""
echo "Then do something like:"
echo "rsync -avx ${RCC_DIR}/  gcompris.net:/var/www/data2/"
#EOF
