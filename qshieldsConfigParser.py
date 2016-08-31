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

#testing = True
testing = False

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

def Random_start():
    return random.randint(1, 100000)

def Write_qsub():
    pass

### Get values from the config file ###

config = configparser.ConfigParser()
config._interpolation = configparser.ExtendedInterpolation()
config.read('qshields.cfg')

# Get general options
Local_Script_Dir = config.get('general_options', 'Local_Script_Dir')
Local_Storage_Dir = config.get('general_options', 'Local_Storage_Dir')

# Get options for qshields
Source = config.get('qshields_options', 'Source')
Source_Location = config.get('qshields_options', 'Source_Location')
Total_Number_Of_Events = int(config.getfloat('qshields_options', 'Total_Number_Of_Events'))
Other_qshields_Parameters = config.get('qshields_options', 'Other_qshields_Parameters')
qshields_Location = config.get('qshields_options', 'qshields_Location')
Simulation_Name = config.get('qshields_options', 'Simulation_Name')

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
g4cuore_Output_Dir = config.get('g4cuore_options', 'g4cuore_Output_Dir')
Input_File_List = config.get('g4cuore_options', 'Input_File_List')
Input_File_List_Size = config.get('g4cuore_options', 'Input_File_List_Size')
Output_File = config.get('g4cuore_options', 'Output_File')
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
Send_Output_To_DB = config.getboolean('database_options', 'Send_Output_To_DB')
DB_Location = config.get('database_options', 'DB_Location')
DB_Username = config.get('database_options', 'DB_Username')
Cluster_Used = config.get('database_options', 'Cluster_Used')
User_Name = config.get('database_options', 'User_Name')
Git_Commit_Hash = config.get('database_options', 'Git_Commit_Hash')
Git_Is_Tag_Version = config.getboolean('database_options', 'Git_Is_Tag_Version')
Git_Tag_Name = config.get('database_options', 'Git_Tag_Name')
qshields_Storage_Location = config.get('database_options', 'qshields_Storage_Location')
Comments = config.get('database_options', 'Comments')


##### End Reading Config File #####

##### Non-Config File Options #####

Date_utc = datetime.datetime.utcnow()
All_g4cuore_Commands = str.join(' ',(Coincidence_Time, Integration_Time, Excluded_Channels, Dead_Time, Pile_Up, Multiplicity_Distance_Cut, Event_Rate, Threshold, Resolution, Other_g4cuore_Parameters))

# Config File Read Testing
if (testing):
    print(Source)
    print(Local_Script_Dir)
    print(Walltime)
    print(Send_Output_To_DB)
    print(Log_File_Dir)
    print(Total_Number_Of_Events)
    print(Number_Of_Jobs)
    print("%s/%s/%s" %(Date_utc.day, Date_utc.month, Date_utc.year))
    print(Input_File_List)
    print(Input_File_List_Size)
    print(Output_File)
    exit(0)
# End Testing

#### Generate scripts #####

# start with blank slate
os.system("clear")

# Create Directories as needed
if not(os.path.isdir(Local_Script_Dir)):
    print("Creating directory %s" %(Local_Script_Dir))
    os.system("mkdir -p %s" %(Local_Script_Dir))
else:
    print("Directory %s exists, continuing" %(Local_Script_Dir))
if not(os.path.isdir(Local_Storage_Dir)):
    print("Creating directory %s" %(Local_Storage_Dir))
    os.system("mkdir -p %s" %(Local_Storage_Dir))
else:
    print("Directory %s exists, continuing" %(Local_Storage_Dir))
if not(os.path.isdir(Root_Output_Dir)):
    print("Creating directory %s" %(Root_Output_Dir))
    os.system("mkdir -p %s" %(Root_Output_Dir))
else:
    print("Directory %s exists, continuing" %(Root_Output_Dir))
if not(os.path.isdir(Log_File_Dir)):
    print("Creating directory %s" %(Log_File_Dir))
    os.system("mkdir -p %s" %(Log_File_Dir))
else:
    print("Directory %s exists, continuing" %(Log_File_Dir))
if not(os.path.isdir("%s/g4cuore" %(Local_Script_Dir))):
    print("Creating directory %s/g4cuore" %(Local_Script_Dir))
    os.system("mkdir -p %s/g4cuore" %(Local_Script_Dir))
else:
    print("Directory %s/g4cuore exists, continuing" %(Local_Script_Dir))

# Check if output locations are empty
Do_qshields = True
if (os.listdir(Root_Output_Dir) or os.listdir(Log_File_Dir)): 
    print("!!!!! WARNING !!!!!")
    print("One or both of Root_Output_Dir or Log_File_Dir are not empty.")
    print("Directories need to be empty to generate qshields pbs scripts.")
    print("Will continue with other options. Empty directories to run qshields!")
    print("!!! END WARNING !!!")
    Do_qshields = False
if Do_qshields:
    # Calculate how many events to put in each job and how many left over
    Number_Of_Events_Per_Job = math.floor(Total_Number_Of_Events / Number_Of_Jobs) + 1 # subtract 1 when counter reaches Events_Leftover
    Events_Leftover = Total_Number_Of_Events % Number_Of_Jobs

    # Get random seed to start with. All jobs with have this + job_number
    Rand_Seed_Start = Random_start()
    if (testing):
        print(Number_Of_Events_Per_Job)
        print(Events_Leftover)

    # The command to run
    Qshields_Command ="{qshields_Location} {Source} {Source_Location} -N $Events {Other_qshields_Parameters} -o'r'{Root_Output_Dir}/{Simulation_Name}_$taskID.root -i $Random_Seed".format(qshields_Location=qshields_Location, Source=Source, Source_Location=Source_Location, Other_qshields_Parameters=Other_qshields_Parameters, Root_Output_Dir=Root_Output_Dir, Simulation_Name=Simulation_Name)
    time.sleep(3)
    print("*"*60)
    print("Generating qshields Command")
    print("The total number of events you are generating is: %s" %(Total_Number_Of_Events))
    print("The qshields command you are generating is:\n%s" %(Qshields_Command))
    print("*"*60)

    # Generate script for PBS Scheduler
    if Batch_Scheduler == "PBS":

        qsub_file = open("%s/%s_%s.pbs" %(Local_Script_Dir, Job_Name, Simulation_Name), "w")
    
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
        
        qsub_file.write("%s\n" %(Qshields_Command))

        ##### Talk to the user ######
        time.sleep(3)
        print("*"*60)
        print("You have generated %s jobs with roughly %s events per job." %(Number_Of_Jobs, Number_Of_Events_Per_Job))
        print("The %s jobs will be output at %s/" %(Batch_Scheduler, Local_Storage_Dir))
        print("The scripts can be run from %s" %(Local_Script_Dir))
        print("You can run the jobs with:\n\t >qsub %s/%s_%s.pbs" %(Local_Script_Dir, Job_Name, Simulation_Name))
        print("*"*60)

##### Options for Saving to DB #####

if Send_Output_To_DB:
    pass


#### Write the g4cuore file ####

g4cuore_file = open("%s/g4cuore/g4cuore.sh" %(Local_Script_Dir), "w")
g4cuore_input_file_list_name = "%s/g4cuore/g4cuore_input_root_file_list.sh" %(Local_Script_Dir)

# The g4cuore command
g4cuore_Command = "{g4cuore_Location} -o'r'{Output_File} -i'l'{g4cuore_input_file_list_name} {Coincidence_Time} {Integration_Time} {Excluded_Channels} {Dead_Time} {Pile_Up} {Multiplicity_Distance_Cut} {Event_Rate} {Threshold} {Resolution} {Other_g4cuore_Parameters}".format(g4cuore_Location=g4cuore_Location.lstrip(), Output_File = Output_File.lstrip(), g4cuore_input_file_list_name = g4cuore_input_file_list_name.lstrip(), Coincidence_Time = Coincidence_Time, Integration_Time = Integration_Time, Excluded_Channels = Excluded_Channels, Dead_Time = Dead_Time, Pile_Up = Pile_Up, Multiplicity_Distance_Cut = Multiplicity_Distance_Cut, Event_Rate = Event_Rate, Threshold = Threshold, Resolution = Resolution, Other_g4cuore_Parameters = Other_g4cuore_Parameters)

g4cuore_file.write("%s \n" %(g4cuore_Command))

# Write the file that contains the names of the .root files

g4cuore_input_file_list = open("%s" %(g4cuore_input_file_list_name), "w")

for i in range (0, Number_Of_Jobs):
    g4cuore_input_file_list.write("%s/%s_%s.root \n" %(Root_Output_Dir, Simulation_Name, i))

# Talk to the user
time.sleep(3)
print("*" * 60)
print("The g4cuore command you are generating is:\n%s" %(g4cuore_Command))
print("The g4cuore command has been written to %s/g4cuore." %(Local_Script_Dir))
print("The g4cuore command will use the files located in %s." %(Root_Output_Dir))
print("You can run the g4cuore command with: \n\t >%s" %(g4cuore_input_file_list_name))
print("*" * 60)


#### Write the mongodb connection file ####

if(Send_Output_To_DB):
    # Connect to DB and open the database and collection
    print("Test1")
    #client = MongoClient('%s' %(DB_Location), 217017)
    client = MongoClient()
    print("Test2")
    db = client.CUORE_MC_database
    collection = db.CUORE_MC_database

    # Create a post to add to the database
    DB_Post = db.CUORE_MC_list

    print(type(Source_Location))

    # if tag version upload this 
    if(Git_Is_Tag_Version):
        post = {"MC Author": User_Name,
                "Cluster Generated From": Cluster_Used,
                "Git Tag": Git_Tag_Name,
                "qshields Storage Location": qshields_Storage_Location,
                "Source": Source,
                "Source Location": Source_Location,
                "Number of Events": Total_Number_Of_Events,
                "Other qshields Parameters": Other_qshields_Parameters,
                "G4cuore Options": All_g4cuore_Commands,
                "Comments": Comments}

    # if not tag version upload this
    else:
        post = {"MC Author": User_Name,
                "Cluster Generated From": Cluster_Used,
                "qshields Git Commit Hash": Git_Commit_Hash,
                "qshields Storage Location": qshields_Storage_Location,
                "Source": Source,
                "Source Location": Source_Location,
                "Number of Events": Total_Number_Of_Events,
                "Other qshields Parameters": Other_qshields_Parameters,
                "G4cuore Options": All_g4cuore_Commands,
                "Comments": Comments}

    # Insert into the collection
    post_id = DB_Post.insert_one(post).inserted_id
    print(post_id)
    print(db.collection_names(include_system_collections=False))
    print(DB_Post.find_one({"_id":post_id}))
