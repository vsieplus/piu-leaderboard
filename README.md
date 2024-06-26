<p>
<img align="left" style="width:92px" src="assets/logo.png" width="92px">

**piu-leaderboard** is a discord bot which monitors the official leaderboards for [Pump it Up Phoenix](https://phoenix.piugame.com/leaderboard/over_ranking.php). The bot offers various commands for querying different chart leaderboards, as well as the ability to track specific players that the bot will automatically send leaderboard updates for.

</p>

---

## Setup

If you are an admin of a discord server and would like to add this bot to your server, you can do so by clicking this [link](https://discord.com/api/oauth2/authorize?client_id=1190188505947701248&permissions=265216&scope=bot). You'll need to have the `Manage Server` permission to do this.

Once the bot is in your server, you should create a new text channel titled `piu-leaderboard`. This is where the bot will post leaderboard updates and where users can interact with the bot. Alternatively, you can opt to create two separate channels: one for leaderboard updates (`piu-leaderboard-updates`), and one for user interaction (`piu-leaderboard-commands`).

## Commands

### Leaderboard Queries
```python
# Query a speicific player's rank on a chart
!queryp <player_id> <chart_id>

# Query a specific rank or range of ranks on a chart
!queryr <rank> <chart_id>

# Query a specific player's pumbility rank
!querypu <player_id>
```

### Player tracking
```python
# Begin tracking a player
!track <player_id>

# Stop tracking a player
!untrack <player_id>

# List all players being currently tracked (server-specific)
!tracking
```

### Parameters

The following parameters are used in some of the commands above. All parameters are case-insensitive.

| Parameter | Description |
| --- | :--- |
| `player_id` | The player's ID on the leaderboard in the format of `name[#tag]`, where `#tag` is the 4-digit discriminator. If `#tag` is not specified, the bot will search for/track all players with the name. To query multiple players at once, use a comma to separate the names ( e.g. `player1,player2` ) |
| `chart_id` | The ID of the chart to query in the format of `"Song title (S/D/Co-op)(Level)"`. This parameter must be enclosed in quotes. For Co-op chart levels, use x2, x3, etc... If an exact match cannot be found, the bot will provide a list of close matches you can choose from. |
| `rank` | The rank or range of ranks to query. To query a range, use the format `rank1-rank2`, where `rank1 < rank2`. Ranks must be between 1 and 100.  |

## Examples

### Querying

#### Query a specific player's rank on a chart

![example1](assets/ex_queryp.png) 

#### Query specific rank placement(s) on a chart

![example2](assets/ex_queryr.png)

### Query a player's pumbility ranking

<img src="assets/ex_querypu.png" width="500">

### Player tracking

#### Start tracking a player...

![example3a](assets/ex_tracking.png)

#### Later on, the bot will automatically send leaderboard/pumbility rank updates for the tracked player(s)...

![example3b](assets/ex_track.png)

## License

This project's code is available under the [MIT license](LICENSE). Feel free to open an issue or pull request if you encounter any issues with the bot, and/or have any suggestions or improvements to offer.

The icons/emojis were taken from the official Pump it Up website and are property of Andamiro. The bot's logo was drawn by me and is free to use 🙂.
