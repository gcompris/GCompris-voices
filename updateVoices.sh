#!/bin/bash
#
# Run this script on gcompris.net to update the rcc files
# being served by it.
#
# cd /opt/gcompris
# ./updateVoices.sh
#
export Qt5_DIR=/usr/lib/x86_64-linux-gnu/qt5

echo "Update gcompris-gtk just in case"
cd gcompris-gtk
git checkout master
git pull

echo "Generate ogg rcc"
cd ../voices/ogg
git pull
./generate_voices_rcc.sh ogg ../../gcompris-gtk/src/lang-activity/resources/lang/words

echo "Create the aac directory"
cd ..
rm -rf aac
rsync -a --exclude .git ogg/ aac
cd aac

echo "Encoding aac files"
./encodeTo.sh aac

echo "Generate aac rcc"
./generate_voices_rcc.sh aac ../../gcompris-gtk/src/lang-activity/resources/lang/words

echo "Consolidate the top level Content file"
cat .rcc/Contents >> ../ogg/.rcc/Contents
rm .rcc/Contents

echo "Update aac on gcompris.net"
rsync -avx .rcc/ /var/www/data2/

echo "Update ogg on gcompris.net"
cd ../ogg
rsync -avx .rcc/ /var/www/data2/
