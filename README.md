This python script executes the following:
1. Connecting with the Windy's API
2. Saving its data to the database file
3. Comparing the recent weather characteristic value with its statistic data.

This script can be launched directly by:
1. Getting an Windy's API key and saving it as an env. variable
2. Installing all the libraries from the requirements.txt file
3. Launching it with all the parameters (see the example in the top of the file).

Docker can be used as an alternative.
To run it in Docker, pull an image from 
docker run -e API_KEY='A1B2C3...' windyapi:v1 .
