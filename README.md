# Discord Reddit Xposter

Dockerized script for crossposting Reddit posts to Discord. Uses PRAW for retrieving posts from Reddit and Discord webhooks with Py-cord to post to Discord.

# Setting up

Clone this git repo (`https://github.com/challos/discord_reddit_xposter`) locally.

## Client

### praw.ini
You'll need a finished praw.ini file, instructions can be found [here](https://praw.readthedocs.io/en/stable/getting_started/quick_start.html). An example file can also be found in the config folder.

### config.ini
You'll also need a config.ini file. The only thing beforehand that you'll need is a list of webhook urls, which you'll put as a comma separated list in the `webhook_urls` argument, as seen in the example_config.ini file.

#### xposter
Just remember to supply a subreddit (multiple subreddit support coming soon), the number of max posts to check for crossposting, how long should be waited before crossposting (in order to prevent spam from being posted to Discord), and how long to wait in between checking for posts that should be crossposted to Discord.
A username and password in this section are not required, but you can set it if you choose to do so.

#### cache
Two types of caches can be chosen, either a local cache for posts that is stored and checked locally, or a REST based cache where the posts can be stored somewhere else. 

All that's needed for a local cache is a username to store posts under, and the `localcache_db_filename` to be set to some filename. Note that in order to ensure persistance across starting and stopping the Docker container, the local database will be stored under the database_folder, where the example_db.db file is.

For the REST cache, the only thing to be done client side is to register a username and password on the server side, specify that server and password under the cache section in the config.ini, and and also specify the url to access the REST cache's webserver. Note that if you are running both the client and server container at the same time, the URL should instead be the `https://server:5000`, as the two containers should be connected by a local bridge network. Otherwise using the normal URL should function fine.

## Server

### config.ini
A config.ini file is also required for the server (and should be under the same directory as the example config file for the server). 

#### database
Change the secretkey of course, but the database URI can stay as is if you desire. It will be saved under the database_folder.

#### xposter
allow_registration should be false unless you're going to be adding a user, to prevent unwanted users on your database (though there shouldn't be any outstanding and terrible security violations if they do).

To register a user to the server, simply use Postman or another REST api program to send a registration request to the server after turning it on (should be basic auth), with the desired username and password. Don't forget to have allow_registration set to True temporarily, or otherwise you'll be refused registration.

# Running

Run `docker-compose up` to run both the client and server if you're using a REST cache, `docker-compose up client` for just the client (potentially with just the local cache), and `docker-compose up server` if you're running just the server.

Tested and works on both WSL2 and Rasbperry Pi 3.

# Potential upcoming features
- [ ] Pip installation
- [ ] Putting the image up on dockerhub?
- [ ] Easier user registration
- [ ] Nicer looking messages when crossposting

# License
