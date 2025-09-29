# Goals of this Project
- Establish and maintain a stable, self-healing connection to an ECU via Bluetooth OBD2 communication tool
- Learn the communication protocol of a Kioti tractor ECU (using the NS4710 as baseline); actively query all PIDs and record responses to a data folder
- Collect data for a cold start with 5 minute warm-up period; idle operations after warm-up for a 2 minute period; varying engine RPM after warm-up for a 2 minute period; operation of hydraulics after warm-up for a 2 minute period; and operation of the PTO for a 30 second period 
- Maintain LOG files with date-time stamp for all operations
- Provision all data for later use in development of a GUI (do not develop the GUI at this time)

# CRITICAL Instructions
- Ensure precautions are implemented to prevent damaging the ECU

# IMPORTANT Instructions
- Increase use of Plan Mode for critical features and functions
- Use a modular approach for different functions of this project
- Default to a single shell setup script, a single python script, and a single succinct markdown instruction file for each module

# General Instructions
- Default to using terminal (CLI) user interface unless otherwise stated

# Workflow
- Start each session with a review of the 3 most recent CHANGELOG files, as available, to determine next steps
- Use gh cli for GitHub operations following standard practices; include GPL-3.0 with Commons Clause license statements in repositories and files
- Create commits at logical completion points: feature completion, bug fixes, or when explicitly requested by user
- Upon receiving the /exit command, create a final commit with CHANGELOG file (date-time stamped) summarizing key changes, what worked, and what didn't work
