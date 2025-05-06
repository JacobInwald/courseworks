echo "$1" > tmp
mv tmp tmp.choc
choco-opt tmp.choc
rm -rf tmp.choc
