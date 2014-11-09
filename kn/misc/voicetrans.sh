#!/bin/sh
mkdir modif
for i in *.wav; do
  sox $i -r 44100 -b 16 modif/$i norm
done

cd modif

oggenc -q0 --downmix -a "shambuk_rajeshwarimk" -d "2014/11/02" -c "copyright=GPL V3+" *.wav

rm *.wav
mv *.ogg ../
rm .voicetrans.sh.swp

cd ../
rm *.wav
rmdir modif
 echo "successfully completed"

