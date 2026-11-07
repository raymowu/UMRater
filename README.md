<a id="readme-top"></a>

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/raymowu/UMRater">
    <img src="https://daisine.github.io/img/mai4.ico" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">UMRater</h3>

  <p align="center">
    A Discord bot to rate and log your favorite anime characters!
    <br />
    <a href="https://discord.com/oauth2/authorize?client_id=1350176544059953293&permissions=8&integration_type=0&scope=bot"><strong>Add to your server! »</strong></a>
    <br />
    <br />
<!--     <a href="">View Demo</a> -->
<!--     &middot; -->
    <a href="https://github.com/raymowu/UMRater/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    &middot;
    <a href="https://github.com/raymowu/UMRater/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
    &middot;
    <a href="https://discord.gg/KrAHvEVS">Join our Discord!</a>
  </p>
</div>

<!-- ABOUT THE PROJECT -->
## About The Project

UMRater is a fun and community-driven Discord bot that lets users rate their favorite characters, compare tastes, and see who truly reigns supreme in the server. Whether you're here to simp respectfully or defend your top-tier character’s honor, this bot brings some friendly rivalry and anime culture straight to your server.

🌸 Features:</br>
📝 Rate any character from Z to F tier</br>
📊 Server-wide aggregated ratings to see who's universally loved (or divisively controversial)</br>
🏆 Top-rated characters</br>
🔍 Search and view character stats</br>
🎉 Perfect for anime-themed servers, community engagement, or just having fun with friends</br>

Bring some character wars to your server and let the ultimate rankings be decided—democracy style.





### Built With

* Discord.py



<!-- USAGE EXAMPLES -->
## Usage

`/add_character_rating <name>`
Shows character stats and information: proceed to give character a rating from the select menu below the panel.

`/get_user_character_ratings <username>`
Gets character ratings from user that were given on current server.

`/get_server_character_ratings`
Shows aggregate character rating data for the current server.





## Deploying to Heroku (GitHub deploys)

This repo is set up for Heroku's Python buildpack: `requirements.txt` (dependencies), `.python-version` (Python 3.13) and a `Procfile` that runs the bot as a `worker` dyno. A Discord bot has no web server, so it can't run as a `web` dyno.

1. In the [Heroku dashboard](https://dashboard.heroku.com/new-app), create a new app.
2. **Deploy** tab → **Deployment method** → **GitHub**, connect your account, then search for and connect `UMRater`.
3. **Settings** tab → **Reveal Config Vars**, and add:
   - `DISCORD_TOKEN`: your bot token
   - `MONGODB_URI`: your MongoDB connection string. If you use MongoDB Atlas, allow access from `0.0.0.0/0` under Network Access, because Heroku dynos don't have fixed IPs.
   - `DB_NAME`: the database name
4. **Deploy** tab → enable **Automatic Deploys** from `main` (optional), or click **Deploy Branch** under Manual deploy.
5. **Resources** tab → turn **off** the `web` dyno if one is listed and turn **on** the `worker` dyno (`python main.py`).
6. Check **More → View logs** for `Connected to MongoDB database!` and `Logged on Discord as ...`.

<!-- CONTACT -->
## Contact

Raymond Wu - [@umarutft](https://twitter.com/umarutft) - rayxrealms@gmail.com

Project Link: [https://github.com/raymowu/UMRater](https://github.com/raymowu/UMRater)





<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

Umaru Doma

<p align="right">(<a href="#readme-top">back to top</a>)</p>
