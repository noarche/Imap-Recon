# Combo Purge

Use this script to create a json database of lines checked, and purge all checked lines from lines that will be checked. 


`python3 main.py -i Wordlist2purge.txt`

If it is the first time using the command the wordlist will be unchanged and saved in ./output/wordlist_{time}.txt. Run the script again and 0 lines will be saved to ./output/wordlist_{timestamp}.txt

# Optional:

Import all checked lines from the past by placing txt files inside checked directory.


# WARNING:

.txt files inside ./checked/ are deleted after import. If you want to keep the files make sure you have another copy BEFORE running the script.