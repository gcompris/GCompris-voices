#!/bin/sh

# First create a new directory
# rsync -a voices.ogg/ voices.aac
# cd voices.aac
# ./encodeToAAC.sh

echo "Transcode ogg files"
for f in $(find . -type f -name \*.ogg)
do
    echo "Processing $f"
    avconv -v warning -i $f -acodec libvo_aacenc ${f%.*}.aac
    rm -f $f
done

echo "Fix symlinks"
for f in $(find . -type l -name \*.ogg)
do
    echo "Processing $f"
    target=$(readlink -f $f)
    rm $f
    ln -s -r ${target%.*}.aac ${f%.*}.aac
done
