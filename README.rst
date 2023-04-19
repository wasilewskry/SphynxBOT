.. raw :: html

    <p align="center">
        <img width="500px" src="https://github.com/wasilewskry/SphynxBOT/blob/master/gallery/logo.png">
    </p>
    <h1 align="center">SphynxBOT</h1>

    <p align="center">
        <a href="https://github.com/wasilewskry/sphynxbot/actions">
            <img alt="Actions Status" src="https://github.com/wasilewskry/sphynxbot/actions/workflows/tests.yaml/badge.svg">
        </a>

        <a href="https://img.shields.io/badge/python-%3E%3D3.10-blue">
            <img alt="Version Support" src="https://img.shields.io/badge/python-%3E%3D3.10-blue">
        </a>
    </p>

SphynxBOT is a multipurpose Discord bot I'm developing for my own use. The project is created with `discord.py <https://github.com/Rapptz/discord.py>`_ and connects to ``PostgreSQL`` database.

Features
--------
* On-demand cinema and TV information with interactive user interface, available through application commands. Provided by `TMDB <https://www.themoviedb.org>`_.
* A system of reminders, including those that fire once and those that repeat periodically at specified time.
* Converting between various units (distance, weight etc).
* Multiple dice rolling functionalities.
* And more to come in the future!

Deploying your own instance
---------------------------

Before you start, make sure you have a compatible version of Python installed.

Obtaining the token
###################

In order to create a bot user on discord you will need to go `here <https://discord.com/developers/applications>`_ and create a new application. Afterwards you can click ``Add Bot`` and copy the bot's token from the next screen.

Environment variables
#####################

Set the following environment variables:

::

    SPHYNX_TOKEN="..."
    SPHYNX_DB_DBNAME="..."
    SPHYNX_DB_HOSTNAME="..."
    SPHYNX_DB_PASSWORD="..."
    SPHYNX_DB_PORT="..."
    SPHYNX_DB_USERNAME="..."

And optionally:

::

    SPHYNX_TMDB_API_KEY="..."

The bot will run without an API key for TMDB but you won't be able to use cinema related commands.

Database
########

If you have Docker installed, the database can be easily deployed by running ``docker compose up`` in the terminal. This is optional and you can provide credentials to your existing Postgres instance instead.

Starting the bot
################

All you need to do now is to install all the required packages with ``pip install requirements.txt`` and execute the ``run.py`` file.

Once the bot is online you need to synchronize application commands defined in the code with Discord by sending the following message:

.. image:: gallery/syncing.png

This only needs to be done once. Available commands are accessed by typing ``/`` into the chat box.
