#!/bin/bash
print_help() {
echo -e "
\033[38;5;141mCOMMAND:\033[0m
   $(basename $0)

\033[38;5;141mARGUMENTS:\033[0m
\t\033[38;5;197m<pos1>\033[0m 	      : Input directory with unsorted DICOMS
\t\033[38;5;197m<pos2>\033[0m 	      : Output directory

\033[38;5;141mUSAGE:\033[0m
    \033[38;5;141m$(basename $0)\033[0m <input_directory>  <outputDirectory>
"
}
if [ $# -lt 2 ]
then
	echo -e "\e[0;31m\n[ERROR]...	A mandatory argument is missing:
      inputDirectory    : $1
      outputDirectory   : $2
      \e[0m"
	print_help
	exit 1
fi

inputDirectory=$1
outputDirectory=$2

C=''; copyLog=''
echo "Getting DICOM information..."
echo "This may take a while."
dicoms=$(find ${inputDirectory} -mindepth 1 -maxdepth 1)
for dicom in $(find ${inputDirectory} -mindepth 1 -maxdepth 1); do
    # Get dicom info
    info=`dcminfo ${dicom}`
    T=`echo "$info" | grep "series" | grep -Eo '[0-9]+/[0-9]+/[0-9]+.*'`
    T2=$(echo $(echo "$T" | awk '{print $1}' | awk -F / '{print $3$2$1}') $(echo "$T" | awk '{print $2}'))
    N=`echo "$info" | grep "series" | awk -F ' ' '{print $2}' | grep -Eo [0-9]+ | awk '{printf("%02d",$1)}'`
    S=`echo "$info" | grep "series" | awk -F ' ' '{print $3}'`
    C=`printf "$C\n$T2 $N $S"`

    copyLog=`printf "$copyLog\n$T2 $N $S $dicom"`
done
copyLog=$(echo "$copyLog" | sed '/^$/d')

# Add session numbers
C2=$(echo "$C" | sort | uniq | sed '/^$/d')
prevId=0; session=1; C3=''

while read -r line; do
    id=`echo $line | awk '{print $3}'`
    id2=`echo $id | sed 's/^0*//'`
    [[ $id2 -lt $prevId ]] && session=$(echo $session + 1 | bc)
    prevId=$id2
    C3=`printf "$C3\n${line} S${session}"`
done <<< "$C2"
C3=$(echo "$C3" | sed '/^$/d')

# Copy to correct directory.
echo "Sorting DICOMS..."
while read -r line; do
    timeStamp=`echo $line | awk '{print $1 " " $2}'`
    num=` echo $line | awk '{print $3}'`
    name=`echo $line | awk '{print $4}'`
    file=`echo $line | awk '{print $5}'`
    directory=`echo "$C3" | grep "$timeStamp" | grep " $num " | grep "$name" |  awk '{print $5 "_" $3 "_" $4}'`

    [[ ! -d "${outputDirectory}/${directory}/" ]] && mkdir -p ${outputDirectory}/${directory}
    cp ${file} ${outputDirectory}/${directory}
done <<< "$copyLog"
