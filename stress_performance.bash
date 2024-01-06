#!/bin/bash

X=10
Y=2

declare -a times

touch testing_flag.txt

poetry run python -u chat/registry.py > registry_output.txt 2>&1 &
registry_pid=$!

while : ; do
    if [ -f registry_output.txt ] && (cat registry_output.txt | grep -q "Server is running"); then
        echo $(cat registry_output.txt | grep "TCP" | awk '{print $5}') > tcp.config
        echo $(cat registry_output.txt | grep "UDP" | awk '{print $5}') > udp.config
        break
    fi 
done

cleanup() {
    kill $registry_pid
    pkill -f chat/peer.py
    [ -f registry_output.txt ] && rm registry_output.txt
    [ -f tcp.config ] && rm tcp.config
    [ -f udp.config ] && rm udp.config
    [ -f testing_flag.txt ] && rm testing_flag.txt
}

trap cleanup EXIT

for i in $(seq 1 $X); do
    poetry run python -u chat/peer.py > /dev/null 2>&1 &

    if [ $i -gt 1 ]; then
        echo -ne "\033[1A\033[2K"
    fi

    echo "Running iteration $i"
    
    start_time=$(date +%s.%N)
    while : ; do
        if grep -q "Connection from:" registry_output.txt; then
            end_time=$(date +%s.%N)
            break
        fi
    done

    times[i]=$(echo "$end_time - $start_time" | bc)

    echo "" > registry_output.txt
done

# print the the whole times array, Y numbers per line
echo "All times for $X instances"
count=0
for time in "${times[@]}"; do
    printf "\033[1;32m%s\033[0ms\t" "$time"
    ((++count % Y == 0)) && echo ""
done
echo ""
echo "=========== Metrics ==========="


echo "Min: $(echo ${times[@]} | tr ' ' '\n' | sort -n | head -n 1 | awk '{printf "\033[1;32m%s\033[0ms\n", $0}')"
echo "Average: $(echo ${times[@]} | tr ' ' '\n' | awk '{sum+=$1} END {print sum/NR}' | awk '{printf "\033[1;32m%s\033[0ms\n", $0}')"
echo "Median: $(echo ${times[@]} | tr ' ' '\n' | sort -n | awk '{a[i++]=$1;} END {print a[int(i/2)];}' | awk '{printf "\033[1;32m%s\033[0ms\n", $0}')"
echo "Max: $(echo ${times[@]} | tr ' ' '\n' | sort -n | tail -n 1 | awk '{printf "\033[1;32m%s\033[0ms\n", $0}')"


# Check if Y is not greater than the length of the array
if [ $Y -gt ${#times[@]} ]; then
    echo "Y is greater than the number of elements in the array."
    exit 1
fi

# Function to calculate average
calculate_average() {
    local -n arr=$1
    local sum=0
    local count=$2

    for (( i=0; i<count; i++ )); do
        sum=$(echo "$sum + ${arr[i]}" | bc)
    done

    echo "$(echo "scale=5; $sum / $count" | bc)"
}

# Calculate the average of the first Y elements and capture the result
first_Y_elements=("${times[@]:0:Y}")
first_Y_avg=$(calculate_average first_Y_elements $Y)

# Calculate the average of the last Y elements and capture the result
last_Y_elements=("${times[@]: -Y}")
last_Y_avg=$(calculate_average last_Y_elements $Y)

# Print the averages
echo -e "Average of the first $Y instances: \033[1;32m$first_Y_avg\033[0ms"
echo -e "Average of the last $Y instances: \033[1;32m$last_Y_avg\033[0ms"

cleanup

