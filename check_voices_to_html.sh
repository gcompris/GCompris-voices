#!/bin/bash
#
# Add the header and footer to an html body
#

LANG=C

cat <<EOF
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
  <meta charset="utf-8"/>
  <title>GCompris Voice Recording Status</title>
</head>
<body>
EOF

while read line
do
  echo "$line"
done < "${1:-/dev/stdin}"

cat <<EOF
<hr></hr>
<p>Page generated the $(date)</p>
</body>
EOF


