from football.models import Team
from django.db.models import Count

# appends new value to the dictionary (unless it is already there)
def append(dict, key, val):
	if dict.has_key(key):
		return dict
	else:
		dict[key] = val
		return dict
	
# does addition to the dictionary item based on key (team)
def add(dict, team, pt):
	if dict.has_key(team):
		dict[team] += pt
	else:
		dict[team] = pt
	return dict
	
# extract every team's number of players from list of scores
def getTeamPlayers(scores):
	teamPlayers = {} # key: team name. value: number of players
	for score in scores:
		if not teamPlayers.has_key(score.home.name):
			teamPlayers[score.home.name] = score.home.players.count()
		if not teamPlayers.has_key(score.away.name):
			teamPlayers[score.away.name] = score.away.players.count()
	return teamPlayers

# gets ranking dictionary for all the teams:
# result: {team name, scored points, played games}
def getRanks(teams=[]):
	if not teams:
		teams = list(Team.objects.all()) # if no teams are passed, all teams in database are analyzed.
	ranks = [] # the result list
	for i in range(len(teams)): # iterating over the teams. Indexes are used here due to dynamicly changed teams list content. Algorithm - simple bubble sort
		team = teams[0] # best ranked team. Team number 1 in beginning.
		pts = -1 # starting points are set to -1
		for t in teams: # now checking every team
			if t.points > pts: # if it's points are greater than current best rank value - this team is recognized as the top team.
				team = t
				pts = team.points
			elif t.points == pts and team!="" and t.games < team.games: # otherwise, checking games (less games, same points -> higher place)
				team = t
				pts = team.points
		ranks.append(team)
		del teams[teams.index(team)] # deleting ranked team and moving on. 
	return ranks	

# gets list of teams by team's players. Only the exact match matters. 
def get_teams_by_players(ids):
	query = Team.objects.annotate(count=Count("players")).filter(count=len(ids)) # first teams with correct number of players are received 
	for _id in ids:
		query = query.filter(players=_id) # then teams are filtered by players ids to get the exact match.
	return query