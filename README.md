## Yes, its a discord bot 🤖

This discord bot attempts to integrate some basic and advanced functionality:

1. Music control + ability to save and load in playlists based on server deployment.
2. The ability to query an AI model hosted at an LMStudio endpoint (easily swappable for Ollama if you know how)
3. Basic moderation functionality

So yeah, thats it for now.

I am working to add more fun activities / systems including the ability to maintain server + user specific contexts for LLM based conversations / roleplay,
and on integrating audio processing for multilingual speech to text!

I also plan on adding a separate logging module that will log user interactions both command specific and channel wide if enabled as such by the server's owner / moderators.

### Setup Instructions

Requires Python 3.10 or newer!

I suggest running the code in a virtual environment as the libraries used are otherwise pretty non essential outside the scope
of this project.

If you do not know how, just run the `setup.bat` file for windows, or `setup.sh` file for Mac / Linux.