Troubleshooting:

Go to the computational_genetic_genealogy directory (Let's call this the working directory):
After you run the git clone command, run the command to list the items in the directory. The command depends on your operating system.
For example, for Windows, run `dir`. For Linux/Ubuntu, run `ls`. You should see `computational_genetic_genealogy` listed.
Navigate into the directory by entering `cd computational_genetic_genealogy`. Running the command to list the items in the directory
this time should show all the files from the repository, including the `instructions` folder.

~/computational_genetic_genealogy>

After you run the Docker image build command

```
docker build -t cgg_image .
```

which runs poetry and install the python packages you need, run

```
poetry run python -m scripts_support.directory_setup
```

This should prompt you in setting up your directories with the final output being similar to the following:

```
Configured directories:
{
  "working_directory": "/home/ubuntu/computational_genetic_genealogy",
  "user_home": "/home/ubuntu",
  "utils_directory": "/home/ubuntu/computational_genetic_genealogy/utils",
  "results_directory": "/home/ubuntu/computational_genetic_genealogy/results",
  "data_directory": "/home/ubuntu/computational_genetic_genealogy/data",
  "references_directory": "/home/ubuntu/computational_genetic_genealogy/references"
}
```

For my system, I'm using user `ubuntu` so my file path is `/home/ubuntu...`. The part leading up 
to `.../computational_genetic_genealogy` should reflect how to navigate to this directory from your computer.

I'm expecting this script to create an .env file in your working directory. 
For me, that places the file here: `/home/ubuntu/computational_genetic_genealogy/.env` and looks like this:

```
PROJECT_UTILS_DIR=/home/ubuntu/computational_genetic_genealogy/utils
PROJECT_RESULTS_DIR=/home/ubuntu/computational_genetic_genealogy/results
PROJECT_DATA_DIR=/home/ubuntu/computational_genetic_genealogy/data
PROJECT_REFERENCES_DIR=/home/ubuntu/computational_genetic_genealogy/references
PROJECT_WORKING_DIR=/home/ubuntu/computational_genetic_genealogy
USER_HOME=/home/ubuntu
```

You'll need this file for your work throughout the semester. 

To start the container, enter
Option 1:

```
docker compose up -d
```

You should see the output in your terminal window indicating that it is started.

Option 2:
Where the file path on the left is my own local directory,
which gets mapped to the file path on the right in the containter.

```
docker run -d \
  --name cgg_container \
  -w /home/ubuntu \
  -v /home/lakishadavid/data:/home/ubuntu/data \
  -v /home/lakishadavid/results:/home/ubuntu/results \
  -v /home/lakishadavid/references:/home/ubuntu/references \
  cgg_image
```

To check to make sure that your container is running:

```
docker ps
```

The output should show you information about the container.

Also run (exactly as seen here):
```
docker compose exec app ls /home/ubuntu/data
docker compose exec app ls /home/ubuntu/results
docker compose exec app ls /home/ubuntu/references
```
You should see outcome list reflect your own directories (which may be empty if you just created it).

You can also start a container shell so that all commands are ran inside the container.
```
docker compose exec app bash
ls /home/ubuntu/data
ls /home/ubuntu/results
ls /home/ubuntu/references
```
Type `exit` to leave the container shell and return to your own shell.

When we run commands in the course, assume that it should be inside the container shell. In other words,
make sure that the container shell is running: `docker compose exec app bash`.
