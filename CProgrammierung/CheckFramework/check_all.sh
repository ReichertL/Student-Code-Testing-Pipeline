#!/bin/bash

# do code similarity tests
# and draw "copy-cat" graphs as well as check simialrity based on 5 severity levels
sh check-plagiarism.sh
rm *.allocated

# build all c files, in the Files/ students directories
find ./Files -type f -name "*.c" -print0 |
while IFS= read -r -d '' pathname; do
    gcc -o "${pathname%.c}.app" "$pathname"
done

# check all compiles programs inside a chroot, and print back result summary file


# chroot it with that command prepended
# chroot chroot_dir 
find ./Files -type f -name "*.c" -print0 |
while IFS= read -r -d '' pathname; do
    /bin/bash -c "valgrind --log-file=\"${pathname%.c}.test1.valgrind\" ./${pathname%.c}.app Tests/input1.data > \"${pathname%.c}.test1.result\""
    /bin/bash -c "valgrind --log-file=\"${pathname%.c}.test2.valgrind\" ./${pathname%.c}.app Tests/input2.data > \"${pathname%.c}.test2.result\""
    echo "T" > $(dirname "${pathname}")/$(grep "total heap usage" "${pathname%.c}.test1.valgrind" | awk '{print $9}').allocated
    #chroot chroot_dir /bin/bash -c "./${pathname%.c}.app Tests/input3.data > \"${pathname%.c}.test3.result\""
    #chroot chroot_dir /bin/bash -c "./${pathname%.c}.app Tests/input4.data > \"${pathname%.c}.test4.result\""
done

find ./Files -type f -name "*.test1.result" -print0 |
while IFS= read -r -d '' pathname; do
    cat $pathname | ./checker.rb Tests/input1.data > "${pathname%.test1.result}.test1.analysis"
done

find ./Files -type f -name "*.test2.result" -print0 |
while IFS= read -r -d '' pathname; do
    cat $pathname | ./checker.rb Tests/input2.data > "${pathname%.test2.result}.test2.analysis"
done


#find ./Files -type f -name "*.test3.result" -print0 |
#while IFS= read -r -d '' pathname; do
#    cat $pathname | ./checker.rb Tests/input3.data > "${pathname%.test3.result}.test3.analysis"
#done
#
#
#find ./Files -type f -name "*.test4.result" -print0 |
#while IFS= read -r -d '' pathname; do
#    cat $pathname | ./checker.rb Tests/input4.data > "${pathname%.test4.result}.test4.analysis"
#done
#echo ""
#echo ""
#echo "ACCEPTS:"
#grep -i accepted Files/* -r 
echo ""
echo ""
echo "REJECTED SOLUTIONS:"
grep -i rejected Files/* -r 

echo ""
echo ""
echo "SAME BYTE ALLOCATIONS:"
dirname=./Files
find $dirname -type f | sed 's_.*/__' | sort|  uniq -d| 
while read fileName
do
find $dirname -type f | grep "$fileName" | grep ".allocated"
done