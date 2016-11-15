#####################################
#                                   #
#    Written by: Christopher Davis  #                           
#    christopher.davis@yale.edu     #
#                                   #
#    10 Aug 2016                    #
#                                   #
#####################################

# Requires Python 3.0 or later

# This program reads the config file qshields.cfg and will generate scripts to be submitted to the PBS batch scheduler

# The first Section deals with the parameters for the qshields application
# The second Section deals with the parameters for the PBS queue
# The third Section deals with the parameters for loading the simulation to the CUORE DB
# The fourth Section deals with the parameters for the g4cuore application

# After the config file is read, the program generates a script that can be submitted to the scheduler as a job array

import sys
if sys.version_info[0] != 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 2):
    print("Sorry, the code requires Python 3.2 or greater")
    print("Exiting...")
    sys.exit(1)

import configparser
import os
import math
import datetime
import random
import time
from pymongo import MongoClient
import getpass

def Random_start():
    return random.randint(1, 100000)

### Get values from the config file ###

config_file_name = "qshields.cfg"

config = configparser.ConfigParser()
config._interpolation = configparser.ExtendedInterpolation()
config.read(config_file_name)

# Get general options
Local_Script_Dir = config.get('general_options', 'Local_Script_Dir')
Config_Script_Dir = config.get('general_options', 'Config_Script_Dir')
Local_Storage_Dir = config.get('general_options', 'Local_Storage_Dir')
Write_qshields = config.getboolean('general_options', 'Write_qshields')
Write_g4cuore = config.getboolean('general_options', 'Write_g4cuore')
Write_to_DB = config.getboolean('general_options', 'Write_to_DB')

# Get options for qshields
qshields_Script_Dir = config.get('qshields_options', 'qshields_Script_Dir')
qshields_Storage_Dir = config.get('qshields_options', 'qshields_Storage_Dir')
Source_Setup_File = config.getboolean('qshields_options', 'Source_Setup_File')
MC_Setup_File = config.get('qshields_options', 'MC_Setup_File')
Source = config.get('qshields_options', 'Source')
Source_Location = config.get('qshields_options', 'Source_Location')
Total_Number_Of_Events = int(config.getfloat('qshields_options', 'Total_Number_Of_Events'))
Other_qshields_Parameters = config.get('qshields_options', 'Other_qshields_Parameters')
qshields_Location = config.get('qshields_options', 'qshields_Location')
qshields_Simulation_Name = config.get('qshields_options', 'qshields_Simulation_Name')

# Get options for Batch Scheduler
Batch_Scheduler = config.get('queue_options', 'Batch_Scheduler')
Queue = config.get('queue_options', 'Queue')
Number_Of_Jobs = config.getint('queue_options', 'Number_Of_Jobs')
if Number_Of_Jobs <=0:
    print("Number Of Jobs must be an integer > 0")
    sys.exit(2)
Job_Name = config.get('queue_options', 'Job_Name')
Root_Output_Dir = config.get('queue_options', 'Root_Output_Dir')
Log_File_Dir = config.get('queue_options', 'Log_File_Dir')
Walltime = config.get('queue_options', 'Walltime')
Email_From_Host = config.get('queue_options', 'Email_From_Host')
User_Email = config.get('queue_options', 'User_Email')

# Get options for g4cuore
g4cuore_Location = config.get('g4cuore_options', 'g4cuore_Location')
g4cuore_Script_Dir = config.get('g4cuore_options', 'g4cuore_Script_Dir')
g4cuore_Storage_Dir = config.get('g4cuore_options', 'g4cuore_Storage_Dir')
Input_File_List = config.get('g4cuore_options', 'Input_File_List')
Input_File_List_Size = config.get('g4cuore_options', 'Input_File_List_Size')
g4cuore_Output_File_Name = config.get('g4cuore_options', 'g4cuore_Output_File_Name')
Coincidence_Time = config.get('g4cuore_options', 'Coincidence_Time')
Integration_Time = config.get('g4cuore_options', 'Integration_Time')
Excluded_Channels = config.get('g4cuore_options', 'Excluded_Channels')
Dead_Time = config.get('g4cuore_options', 'Dead_Time')
Pile_Up = config.get('g4cuore_options', 'Pile_Up')
Multiplicity_Distance_Cut = config.get('g4cuore_options', 'Multiplicity_Distance_Cut')
Event_Rate = config.get('g4cuore_options', 'Event_Rate')
Threshold = config.get('g4cuore_options', 'Threshold')
Resolution = config.get('g4cuore_options', 'Resolution')
Other_g4cuore_Parameters = config.get('g4cuore_options', 'Other_g4cuore_Parameters')

# Get options for DB upload
DB_Script_Dir = config.get('database_options', 'DB_Script_Dir')
DB_Location = config.get('database_options', 'DB_Location')
DB_Port = config.get('database_options', 'DB_Port')
DB_Database = config.get('database_options', 'DB_Database')
DB_Collection = config.get('database_options', 'DB_Collection')
DB_Username = config.get('database_options', 'DB_Username')
Cluster_Used = config.get('database_options', 'Cluster_Used')
User_Name = config.get('database_options', 'User_Name')
Date_Generated = config.get('database_options', 'Date_Generated')
Git_Commit_Hash = config.get('database_options', 'Git_Commit_Hash')
Git_Is_Tag_Version = config.getboolean('database_options', 'Git_Is_Tag_Version')
Git_Tag_Name = config.get('database_options', 'Git_Tag_Name')
qshields_Storage_Location = config.get('database_options', 'qshields_Storage_Location')
Comments = config.get('database_options', 'Comments')

#### Checks on Config File inputs ####

if(Write_qshields):
    if(Source_Setup_File):
        while True:
            try:
                f = open(MC_Setup_File, 'r')
            except IOError:
                print("Cannot open %s" %(MC_Setup_File))
            else:
                f.close()
                break

    if not(os.path.exists(qshields_Location)):
        print("A file does not exist at location %s" %(qshields_Location))
        print("Exiting...")
        sys.exit(2)

if(Write_g4cuore):
    if not(os.path.exists(g4cuore_Location)):
        print("A file does not exist at location %s"(g4cuore_Location))
        print("Exiting...")
        sys.exit(2)

##### End Reading Config File #####

##### Non-Config File Options #####

Date_utc = datetime.datetime.utcnow()
All_g4cuore_Commands = str.join(' ',(Coincidence_Time, Integration_Time, Excluded_Channels, Dead_Time, Pile_Up, Multiplicity_Distance_Cut, Event_Rate, Threshold, Resolution, Other_g4cuore_Parameters))

#### Generate scripts #####

# start with blank slate
os.system("clear")

# Create Directories as needed
while True:

    try:

        print("Generating Directories as needed")
        if not(os.path.isdir(Local_Script_Dir)):
            os.system("mkdir -p %s" %(Local_Script_Dir))
            print("Directory %s generated" %(Local_Script_Dir))
        else:
            print("Directory %s exists, continuing" %(Local_Script_Dir))
        if not(os.path.isdir(Config_Script_Dir)):
            os.system("mkdir -p %s" %(Config_Script_Dir))
            print("Directory %s generated" %(Config_Script_Dir))
        else: 
            print("Directory %s exists, continuing" %(Config_Script_Dir))
        if not(os.path.isdir(Local_Storage_Dir)):
            os.system("mkdir -p %s" %(Local_Storage_Dir))
            print("Directory %s generated" %(Local_Storage_Dir))
        else:
            print("Directory %s exists, continuing" %(Local_Storage_Dir))
        if(Write_qshields):
            if not(os.path.isdir(Root_Output_Dir)):
                os.system("mkdir -p %s" %(Root_Output_Dir))
                print("Directory %s generated" %(Root_Output_Dir))
            else:
                print("Directory %s exists, continuing" %(Root_Output_Dir))
            if not(os.path.isdir(Log_File_Dir)):
                os.system("mkdir -p %s" %(Log_File_Dir))
                print("Directory %s generated" %(Log_File_Dir))
            else:
                print("Directory %s exists, continuing" %(Log_File_Dir))
            if not(os.path.isdir("%s" %(qshields_Script_Dir))):
                os.system("mkdir -p %s" %(qshields_Script_Dir))
                print("Directory %s generated" %(qshields_Script_Dir))
            else:
                print("Directory %s exists, continuing" %(qshields_Script_Dir))
            if not(os.path.isdir("%s" %(qshields_Storage_Dir))):
                os.system("mkdir -p %s" %(qshields_Storage_Dir))
                print("Directory %s generated" %(qshields_Storage_Dir))
            else: 
                print("Directory %s exists, continuing" %(qshields_Storage_Dir))
        if(Write_g4cuore):
            if not(os.path.isdir("%s" %(g4cuore_Script_Dir))):
                os.system("mkdir -p %s" %(g4cuore_Script_Dir))
                print("Directory %s generated" %(g4cuore_Script_Dir))
            else:
                print("Directory %s exists, continuing" %(g4cuore_Script_Dir))
            if not(os.path.isdir("%s" %(g4cuore_Storage_Dir))):
                os.system("mkdir -p %s" %(g4cuore_Storage_Dir))
                print("Directory %s generated" %(g4cuore_Storage_Dir))
            else: 
                print("Directory %s exists, continuing" %(g4cuore_Storage_Dir))
        if(Write_to_DB):
            if not(os.path.isdir("%s" %(DB_Script_Dir))):
                os.system("mkdir -p %s" %(DB_Script_Dir))
                print("Directory %s generated" %(DB_Script_Dir))
            else:
                print("Directory %s exists, continuing" %(DB_Script_Dir))

    except: 
        print("Error creating directories. Check to make sure you have permissions to write here")
    else:
        print("Directory generation complete")
        break

# Copy config file to destination
os.system("cp %s %s/." %(config_file_name, Config_Script_Dir))
    
# Check if output locations are empty
if(Write_qshields):
    if (os.listdir(Root_Output_Dir) or os.listdir(Log_File_Dir)): 
        print("!!!!! WARNING !!!!!")
        print("One or both of %s or %s not empty." %(Root_Output_Dir, Log_File_Dir))
        print("Directories need to be empty to generate qshields pbs scripts.")
        print("Will continue with other options. Empty directories to run qshields!")
        print("!!! END WARNING !!!")
        Write_qshields = False

if not (Write_qshields):
    print("Skipping qshields")
    print("*"*60)
else:
    # Calculate how many events to put in each job and how many left over
    Number_Of_Events_Per_Job = math.floor(Total_Number_Of_Events / Number_Of_Jobs) + 1 # subtract 1 when counter reaches Events_Leftover
    Events_Leftover = Total_Number_Of_Events % Number_Of_Jobs

    # Get random seed to start with. All jobs with have this + job_number
    Rand_Seed_Start = Random_start()

    # The command to run
    Qshields_Command ="{qshields_Location} {Source} {Source_Location} -N $Events {Other_qshields_Parameters} -o'r'{Root_Output_Dir}/{qshields_Simulation_Name}_$taskID.root -i $Random_Seed".format(qshields_Location=qshields_Location, Source=Source, Source_Location=Source_Location, Other_qshields_Parameters=Other_qshields_Parameters, Root_Output_Dir=Root_Output_Dir, qshields_Simulation_Name=qshields_Simulation_Name)
    time.sleep(3)
    print("*"*60)
    print("Generating qshields Command")
    print("The total number of events you are generating is: %s" %(Total_Number_Of_Events))
    print("The qshields command you are generating is:\n%s" %(Qshields_Command))
    print("*"*60)

    # Generate script for PBS Scheduler
    if Batch_Scheduler == "PBS":

        qsub_file = open("%s/%s_%s.pbs" %(qshields_Script_Dir, Job_Name, qshields_Simulation_Name), "w")
    
        qsub_file.write("#PBS -N %s\n" %(Job_Name))
        qsub_file.write("#PBS -S /bin/bash\n")
        qsub_file.write("#PBS -q %s\n" %(Queue))
        qsub_file.write("#PBS -l walltime=%s nodes=1:ppn=1\n" %(Walltime))
        qsub_file.write("#PBS -M %s\n" %(User_Email))
        qsub_file.write("#PBS -m %s\n" %(Email_From_Host))
        qsub_file.write("#PBS -o %s/\n" %(Log_File_Dir))
        qsub_file.write("#PBS -e %s/\n" %(Log_File_Dir))
        qsub_file.write("#PBS -t 0-%s\n" %(Number_Of_Jobs-1))
        
        qsub_file.write("taskID=$PBS_ARRAYID\n")
        qsub_file.write("Events_Leftover=%s\n" %(Events_Leftover))
        qsub_file.write("Events=%s\n" %(Number_Of_Events_Per_Job))
        qsub_file.write("if [ \"$taskID\" -ge \"$Events_Leftover\" ]; then\n")
        qsub_file.write("\tEvents=%s\n" %(Number_Of_Events_Per_Job - 1))
        qsub_file.write("fi\n")
        qsub_file.write("Random_Seed=%s\n" %(Rand_Seed_Start))
        qsub_file.write("Random_Seed=$((Random_Seed + $taskID))\n")
        
        if(Source_Setup_File):
            qsub_file.write("source %s\n" %(MC_Setup_File))
        
        qsub_file.write("%s\n" %(Qshields_Command))

        ##### Talk to the user ######
        time.sleep(3)
        print("*"*60)
        print("You have generated %s jobs with roughly %s events per job." %(Number_Of_Jobs, Number_Of_Events_Per_Job - 1))
        print("The %s jobs will be output at %s/" %(Batch_Scheduler, Local_Storage_Dir))
        print("The scripts can be run from %s" %(qshields_Script_Dir))
        print("You can run the jobs with:\n\t >qsub %s/%s_%s.pbs" %(Local_Script_Dir, Job_Name, qshields_Simulation_Name))
        print("*"*60)

    hadd_file = open("%s/hadd.sh" %(qshields_Script_Dir), "w")

    hadd_file.write("echo 'This script will now collect the partial root files into a singe file'\n")
    hadd_file.write("echo 'It may be prudent to run this script on a compute node, as this may take a while'\n")
    
    # loop over set number of output files at a time, adding them to a tmp file, and then repeating

    # Set number of files per hadd job to be 100
    hadd_step_jobs = 100
    hadd_full_steps = math.floor(float(Number_Of_Jobs / hadd_step_jobs))
    hadd_last_step = Number_Of_Jobs % hadd_step_jobs


    for i in range (0, hadd_full_steps):
        hadd_file.write("hadd %s/tmp_%s.temp " %(qshields_Storage_Dir, i))
        for j in range (0, hadd_step_jobs):
            root_part = i * 100 + j 
            hadd_file.write("%s/%s_%s.root " %(Root_Output_Dir, qshields_Simulation_Name, root_part))
        hadd_file.write("\n")

    hadd_file.write("hadd %s/tmp_%s.temp " %(qshields_Storage_Dir, hadd_full_steps))
    for l in range (0, hadd_last_step):
        root_part = hadd_full_steps * 100 + l
        hadd_file.write("%s/%s_%s.root " %(Root_Output_Dir, qshields_Simulation_Name, root_part))

    hadd_file.write("\n")
    hadd_file.write("hadd %s/%s.root %s/*.temp \n" %(qshields_Storage_Dir, qshields_Simulation_Name, qshields_Storage_Dir))
    hadd_file.write("rm %s/*.temp \n" %(qshields_Storage_Dir))
    hadd_file.write("echo 'root file collection complete' \n")
    
##### Options for Saving to DB #####


#### Write the g4cuore file ####
if not (Write_g4cuore):
    print("Skipping g4cuore...")
    print("*"*60)
else:

    g4cuore_file = open("%s/g4cuore.sh" %(g4cuore_Script_Dir), "w")
    g4cuore_input_file_list_name = "%s/g4cuore_input_root_file_list.sh" %(g4cuore_Script_Dir)

    # The g4cuore command
    g4cuore_Command = "{g4cuore_Location} -o'r'{g4cuore_Storage_Dir}/{g4cuore_Output_File_Name} -i'l'{g4cuore_input_file_list_name} {Coincidence_Time} {Integration_Time} {Excluded_Channels} {Dead_Time} {Pile_Up} {Multiplicity_Distance_Cut} {Event_Rate} {Threshold} {Resolution} {Other_g4cuore_Parameters}".format(g4cuore_Location=g4cuore_Location.lstrip(), g4cuore_Storage_Dir=g4cuore_Storage_Dir.lstrip(), g4cuore_Output_File_Name = g4cuore_Output_File_Name.lstrip(), g4cuore_input_file_list_name = g4cuore_input_file_list_name.lstrip(), Coincidence_Time = Coincidence_Time, Integration_Time = Integration_Time, Excluded_Channels = Excluded_Channels, Dead_Time = Dead_Time, Pile_Up = Pile_Up, Multiplicity_Distance_Cut = Multiplicity_Distance_Cut, Event_Rate = Event_Rate, Threshold = Threshold, Resolution = Resolution, Other_g4cuore_Parameters = Other_g4cuore_Parameters)

    g4cuore_file.write("%s \n" %(g4cuore_Command))
    
    # Write the file that contains the names of the .root files
    
    g4cuore_input_file_list = open("%s" %(g4cuore_input_file_list_name), "w")

    for i in range (0, Number_Of_Jobs):
        g4cuore_input_file_list.write("%s/%s_%s.root \n" %(Root_Output_Dir, qshields_Simulation_Name, i))

    # Talk to the user
    time.sleep(3)
    print("*" * 60)
    print("The g4cuore command you are generating is:\n%s" %(g4cuore_Command))
    print("The g4cuore command has been written to %s" %(g4cuore_Script_Dir))
    print("The g4cuore command will use the files located in %s" %(Root_Output_Dir))
    print("The output file will be written to %s/%s" %(g4cuore_Storage_Dir, g4cuore_Output_File_Name))
    print("You can run the g4cuore command with: \n\t >%s/g4cuore.sh" %(g4cuore_Script_Dir))
    print("*" * 60)
    

#### Write the mongodb connection file ####
if not (Write_to_DB):
    print("Skipping DB entry...")
    print("*"*60)
if (Write_to_DB):

    db_file = open("%s/db_upload.py" %(DB_Script_Dir), "w")

    # Edit the qshields parameters to make them look nicer in the database
    Source_Location = Source_Location.replace("\\","")
    Other_qshields_Parameters = Other_qshields_Parameters.replace("\\","")

    # Write the file to be run:
    db_file.write("""#run with python3.5 {DB_SCRIPT_DIR}/db_upload.py
import sys
if sys.version_info[0] != 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 2):
\tprint("Sorry, the code requires Python 3.2 or greater")
\tprint("Exiting...")
\tsys.exit(1)
import configparser
import os
import math
import datetime
import random
import time
from pymongo import MongoClient
import getpass

\t# Connect to DB and open the database and collection
password = getpass.getpass('Password for DB (\"Pl*****\"): ')
client = MongoClient('mongodb://{DB_USERNAME}:%s@localhost:{DB_PORT}/' %(password))
del password
db = client.{DB_DATABASE}
collection = db.{DB_DATABASE}

\t# Create a post to add to the database
DB_Post = db.{DB_COLLECTION}
""".format(DB_SCRIPT_DIR=DB_Script_Dir, DB_USERNAME=DB_Username, DB_PORT=DB_Port, DB_DATABASE=DB_Database, DB_COLLECTION=DB_Collection))

    # if tag version upload this
    if(Git_Is_Tag_Version):
        db_file.write("""post = {{
\t"MC Author": "{USER_NAME}",
\t"Date Generated": "{DATE_GENERATED}",
\t"Cluster Generated From": "{CLUSTER_USED}",
\t"Git Tag": "{GIT_TAG_NAME}",
\t"qshields Storage Location": "{QSHIELDS_STORAGE_DIR}",
\t"qshields simulation name": "{QSHIELDS_SIMULATION_NAME}",
\t"g4cuore Storage Location": "{G4CUORE_STORAGE_DIR}",
\t"Source": "{SOURCE}",
\t"Source Location": "{SOURCE_LOCATION}",
\t"Number of Events":" {TOTAL_NUMBER_OF_EVENTS}",
\t"Other qshields Parameters": "{OTHER_QSHIELDS_PARAMETERS}",
\t"G4cuore Options": "{ALL_G4CUORE_COMMANDS}",
\t"Comments": "{COMMENTS}"}}
""".format(USER_NAME=User_Name, DATE_GENERATED=Date_Generated, CLUSTER_USED=Cluster_Used, GIT_TAG_NAME=Git_Tag_Name, QSHIELDS_STORAGE_DIR=qshields_Storage_Dir, QSHIELDS_SIMULATION_NAME=qshields_Simulation_Name, G4CUORE_STORAGE_DIR=g4cuore_Storage_Dir, SOURCE=Source, SOURCE_LOCATION=Source_Location, TOTAL_NUMBER_OF_EVENTS=Total_Number_Of_Events, OTHER_QSHIELDS_PARAMETERS=Other_qshields_Parameters, ALL_G4CUORE_COMMANDS=All_g4cuore_Commands, COMMENTS=Comments))

    # if not tag version upload this
    else:
        db_file.write("""post = {{
\t"MC Author": "{USER_NAME}",
\t"Date Generated": "{DATE_GENERATED}",
\t"Cluster Generated From": "{CLUSTER_USED}",
\t"qshields Git Commit Hash": "{GIT_COMMIT_HASH}",
\t"qshields Storage Location": "{QSHIELDS_STORAGE_DIR}",
\t"qshields Simulation Name": "{QSHIELDS_SIMULATION_NAME}",
\t"g4cuore Storage Location": "{G4CUORE_STORAGE_DIR}",
\t"Source": "{SOURCE}",
\t"Source Location": "{SOURCE_LOCATION}",
\t"Number of Events": "{TOTAL_NUMBER_OF_EVENTS}",
\t"Other qshields Parameters": "{OTHER_QSHIELDS_PARAMETERS}",
\t"G4cuore Options": "{ALL_G4CUORE_COMMANDS}",
\t"Comments": "{COMMENTS}"}}
""".format(USER_NAME=User_Name, DATE_GENERATED=Date_Generated, CLUSTER_USED=Cluster_Used, GIT_COMMIT_HASH=Git_Commit_Hash, QSHIELDS_STORAGE_DIR=qshields_Storage_Dir, QSHIELDS_SIMULATION_NAME=qshields_Simulation_Name, G4CUORE_STORAGE_DIR=g4cuore_Storage_Dir, SOURCE=Source, SOURCE_LOCATION=Source_Location, TOTAL_NUMBER_OF_EVENTS=Total_Number_Of_Events, OTHER_QSHIELDS_PARAMETERS=Other_qshields_Parameters, ALL_G4CUORE_COMMANDS=All_g4cuore_Commands, COMMENTS=Comments))

    db_file.write("""# Insert into the collection
post_id = DB_Post.insert_one(post).inserted_id

print(post_id)
#print(db.collection_names(include_system_collections=False))
print(DB_Post.find_one({"_id":post_id}))
""")

                  
# Talk to the user
    time.sleep(3)
    print("*" * 60)
    print("The script to insert the MC info to the Database has been written to %s/db_upload.py" %(DB_Script_Dir))
    print("You can run the upload script with (python 3.2 or greater): \n\t >python %s/db_upload.py" %(DB_Script_Dir))
    print("*" * 60)


print("*"*60)
print("Script generation complete")
print("*"*60)
