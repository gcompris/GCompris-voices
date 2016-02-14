#!/bin/sh

# First create a new directory (aac ac3 mp3)
# Example for aac:
# rsync -a --exclude .git voices.ogg/ voices.aac
# cd voices.aac
# ./encodeTo.sh

if [ $# -ne 1 ]
then
  echo "Usage $(basename $0) aac|ac3|mp3"
  exit 1
fi

if [ ! -d af ]
then
  echo "ERROR: move to the voice directory first"
  exit 1
fi

format=$1

if [ $format = "aac" ]
then
  codec="libvo_aacenc"
elif [ $format = "ac3" ]
then
  codec="ac3"
elif [ $format = "mp3" ]
then
  codec="libmp3lame"
else
  echo "Error, unsupported format $1"
  exit 1
fi

echo "Transcode ogg files to $format"
for f in $(find . -type f -name \*.ogg)
do
    #echo "Processing $f"
    avconv -v warning -i $f -acodec $codec ${f%.*}.${format}
    if [ $? -ne 0 ]
    then
       echo "ERROR: Failed to convert $f"
    fi
    rm -f $f
done

echo "Fix symlinks"
for f in $(find . -type l -name \*.ogg)
do
    #echo "Processing $f"
    target=$(readlink -f $f)
    rm $f
    ln -s -r ${target%.*}.${format} ${f%.*}.${format}
done
