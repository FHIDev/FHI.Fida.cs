#!/bin/bash

# Check if the number of arguments is correct
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <username> <uid>"
    exit 1
fi

username="$1"
uid="$2"
home_dir="/home/$username"

# Check if the user exists
if id "$username" &>/dev/null; then
    echo "User $username exists."
else
    # Create the user without creating the home directory
    useradd -M -s /bin/bash -u "$uid" "$username"
    echo "User $username created without home directory."
fi

# Check if the home directory exists
if [ ! -d "$home_dir" ]; then
    # Create the home directory
    mkdir -p "$home_dir"
    echo "Home directory $home_dir created."
else
    echo "Home directory $home_dir already exists."
fi

# Check if the sc9example directory exists
if [ ! -d "$home_dir/cs9example" ]; then
    # Create the home directory
    cp -r /cs9example "$home_dir/"
    echo "Copied /cs9example"
fi

# Set appropriate permissions and ownership for the home directory
chmod 777 "$home_dir"
chown -R "$username:$username" "$home_dir"

echo "Permissions and ownership set for $home_dir."
