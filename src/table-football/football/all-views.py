from django import forms
from django.shortcuts import render_to_response
from django.template import RequestContext
from football.models import Score, Player, Team
from django.views.generic import TemplateView, View
from django.db.models import Q, Count
from datetime import date, timedelta
from pylab import figure, barh, yticks, xlabel, title, grid, savefig, arange, ylabel, clf

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
	
################################################
	
# The main window view
class Home(TemplateView):
	template_name = "index.html"
	
	# Score form
	class InputScore(forms.ModelForm):		
		def __init__(self, *args, **kwargs):
			super(Home.InputScore, self).__init__(*args, **kwargs)
		class Meta:
			model = Score
			exclude = ('home','away','when') #disabling fields, that will be filled from other places
	
	# Home team input form
	class HomeTeam(forms.ModelForm):
		def __init__(self, *args, **kwargs):
			super(Home.HomeTeam, self).__init__(*args, **kwargs)
		class Meta:
			model = Team
			exclude = ('points', 'games') # points and games are created/updated automatically 
			
	# Away team input form. Same as home team, only for the opposition
	class AwayTeam(forms.ModelForm):
		def __init__(self, *args, **kwargs):
			super(Home.AwayTeam, self).__init__(*args, **kwargs)
		class Meta:
			model = Team
			exclude = ('points', 'games')
	
	# makes a team name based on list of players or uses a teamName
	def makeTeamName(self, teamName, players):
		if teamName == '':
			for pl in players:
				teamName += pl.name + "+" # format: player1 + player2 + ...
			teamName = teamName[:-1] # removing last plus
		return teamName

	# showing the first screen
	def get(self, request, *args, **kwargs):
		context = {}
		context['title'] = "Home"
		context['scoreForm'] = self.InputScore() 
		context['homeTeamForm'] = self.HomeTeam(prefix="h") #preifx is used to distinguish to team objects. h for Home. a for Away.
		context['awayTeamForm'] = self.AwayTeam(prefix="a")
		scores = Score.objects.all()
		context['scores'] = scores
		ranks = getRanks()
		context['ranks'] = ranks;
		return self.render_to_response(context)
	
	# determines points of the home team of the score
	def getHomePoints(self, score):
		points = 0
		if score.home_score > score.away_score:
			points = 2
		if score.home_score == score.away_score:
			points = 1
		return points
		
	# determines points of away team of the score
	def getAwayPoints(self, score):
		points = 0
		if score.home_score < score.away_score:
			points = 2
		if score.home_score == score.away_score:
			points = 1
		return points
		
	# gets the team and immediately updates it. If team for provided places doesn't exist - new team is created.
	def getTeam(self, players, form, points):
		teams = get_teams_by_players(list(p.id for p in players))
		if not teams:
			name = self.makeTeamName(form.cleaned_data['name'], players) # determining team name
			team = form.save(commit=False) # making team object
			team.name = name
			team.points = points
			team.games = 1
			try: # actual saving of new team
				team.save()
				form.save_m2m() # do not forget m2m (players)
			except: 
				team.delete() # if any errors appear - make sure no garbage is left.
				return ''
		else: # simple update
			team = teams[0]
			team.points = team.points+points
			team.games = team.games+1
			team.save()
		return team
			
	# Updates chart. pylab's charting module is used here.
	def updateChart(self, ranks):
		teams = [] # y axis
		points = [] # x axis
		for rank in reversed(ranks): # generating axes values 
			teams.append(rank.name)
			points.append(rank.points)
		pos = arange(len(teams))+.5    # the bar centers on the y axis
		figure(1) 
		barh(pos, points, align='center') # used horizontal bar graph
		yticks(pos, teams)
		xlabel('Points')
		ylabel('Team')
		title('Ranking')
		grid(True)
		savefig("pics/chart.png", dpi=60) # saving chart in pics folder to show it later.
		clf() # don't forget to clear the figure to make a blank start for the next chart.
	
	# posting the form data, creating scores objects and updating teams, charts, ranks.
	def post(self, request, *args, **kwargs):
		msg = '' # happy message
		error = '' # error message
		save = 0 # do we save score object?
		scoreForm = self.InputScore(request.POST) #getting form data from the post request
		homeTeamForm = self.HomeTeam(request.POST, prefix="h")
		awayTeamForm = self.AwayTeam(request.POST, prefix="a")
		if scoreForm.is_valid() and homeTeamForm.is_valid() and awayTeamForm.is_valid(): # validating data
			save = 1 # data is ok - so probably we can save it
			newScore = scoreForm.save(commit=False) # creating new score object from form data
			newScore.when = date.today() # setting it's date for today
			homeTeamPlayers = homeTeamForm.cleaned_data['players'] # getting lists of home
			awayTeamPlayers = awayTeamForm.cleaned_data['players'] # and away players
			for pl in homeTeamPlayers:
				if pl in awayTeamPlayers:
					error = pl.name + ' is on both teams!' # checking, if someone doesn't try to play for both teams at the same time.
					save = 0 # disabling save in that case.
			if len(homeTeamPlayers) > 3 or len(awayTeamPlayers) > 3 or len(homeTeamPlayers)+len(awayTeamPlayers) == 5:
				save = 0 # checking the possible match formats. 
				error = 'Possible matches: 1 vs. 1, 2 vs. 2, 3 vs. 3, 1 vs. 2';
			elif save <> 0: # if save is allowed
				homeTeam = self.getTeam(homeTeamPlayers, homeTeamForm, self.getHomePoints(newScore)) # getting teams 
				awayTeam = self.getTeam(awayTeamPlayers, awayTeamForm, self.getAwayPoints(newScore)) # and updating them at the same time.
				if homeTeam == '' or awayTeam == '': #when no team comes, 
					msg = 'Team with the same name exists' #team with same name exists.
				else:
					newScore.home = homeTeam #referencing teams from score object.
					newScore.away = awayTeam
					newScore.save() #and finally saving new score.
					msg = 'Saved'
		else:
			error = 'Wrong values' # error message, when input form has errors.
		scores = Score.objects.all() #getting all scores to display them on the page.
		ranks = getRanks(); #same for ranks, but since ranks are not stored, they are generated from team objects to get the most accurate data.
		if save:
			self.updateChart(ranks) #updating chart, only when some score was saved.
		
		return render_to_response('index.html', {
			'scoreForm': scoreForm, # form to display score input
			'homeTeamForm' : homeTeamForm, # players selection and team name
			'awayTeamForm' : awayTeamForm,
			'msg' : msg, # info message
			'error' : error, # error message
			'scores' : scores, # score history
			'ranks' : ranks, # ranks sorted by points
			'title' : 'Home' # title of the page
		}, context_instance=RequestContext(request))
	
####################################################
	
class TeamProfile(TemplateView):
	# shows team info
    template_name = "team.html"

    def get_context_data(self, **kwargs):
		context = super(TeamProfile, self).get_context_data(**kwargs)
		teamId = kwargs['team'] # team id is passed by argument
		team = Team.objects.get(pk=teamId) # teams is selected by id
		if team: # if team was successfully selected its profile is shown
			context['team'] = team # to gather data from team object
			scores = Score.objects.filter(Q(home=teamId) | Q(away=teamId) ) # scores, where team is either home team or away team. 
			context['scores'] = scores 
			stats = {} # dict for different statistics
			stats["games"] = team.games; 
			won = 0
			lost = 0
			draw = 0
			goals_scored = 0
			opponent_goals = 0
			milestones = {} # dict for interesting events
			biggestWin = "" # for corresponding score object
			bw = 0 # the biggest win counter
			biggestLoss = ""
			bl = 0
			mostGoalsScored = ""
			mgs = 0
			mostGoalsReceived = ""
			mgr = 0
			for score in scores:
				# local variables, compared with the biggest/most values.
				w = 0
				l = 0
				gs = 0
				og = 0
				if str(score.home.id) == teamId:
					if score.home_score > score.away_score:
						w = 1
					elif score.home_score < score.away_score:
						l = 1
					gs = score.home_score
					og = score.away_score
				else:
					if score.home_score < score.away_score:
						w = 1
					elif score.home_score > score.away_score:
						l = 1
					gs = score.away_score
					og = score.home_score
				dif = abs(score.home_score - score.away_score) # the difference between scores.
				if w:
					won = won + 1
					score.color = "green" # green color for victory. Color is passed on to the view to determine the color of the text
					if dif > bw:
						bw = dif
						biggestWin = score
				elif l:
					lost = lost + 1
					score.color = "red" # red for loss
					if dif > bl:
						bl = dif
						biggestLoss = score
				else:
					draw = draw + 1
					score.color = "blue" # blue for draw
				goals_scored = goals_scored + gs
				opponent_goals = opponent_goals + og
				if gs > mgs:
					mgs = gs
					mostGoalsScored = score
				if og > mgr:
					mgr = og
					mostGoalsReceived = score
			stats["won"] = won
			stats["lost"] = lost
			stats["draw"] = draw
			stats["gs"] = goals_scored
			stats["og"] = opponent_goals
			context['stats'] = stats
			milestones['bw'] = biggestWin
			milestones['bl'] = biggestLoss
			milestones['mgs'] = mostGoalsScored
			milestones['mgr'] = mostGoalsReceived
			context["milestones"] = milestones
			context["points"] = team.points
		else:
			context['error'] = 'No team with Id <b>' + teamId + '</b>'
		context['title'] = 'Team Profile: ' + team.name
		return context

###################################################
		
import itertools
class MatchMaker(TemplateView):
	# makes the best teams for given number of players.
	template_name = "maker.html"
	
	class MakerForm(forms.Form):
		players = forms.IntegerField(min_value=2) # form to input number of players
	
	# initialy there is only a form and page title
	def get(self, request, *args, **kwargs):
		context = {} 
		context['title'] = "MatchMaker"
		context['form'] = self.MakerForm()
		return self.render_to_response(context)
			
	def post(self, request, *args, **kwargs):
		error = ''
		msg = ''
		form = self.MakerForm(request.POST)
		if form.is_valid():
			players = form.cleaned_data['players']
			if (players <= 4 and players > 1) or players == 6: # checking number of players to match possible combinations
				# there can be 3 types of teams: one player, two players and three players
				onePlayerTeams = {}
				twoPlayerTeams = {}
				threePlayerTeams = {}
				allPlayers = list(Player.objects.all())
				if len(allPlayers) < players: # there might be not enough players in the database for the desired matchup
					error = "Not enough players (need " + str(players) + ", have " + str(len(allPlayers)) + ")"
				else:
					teams = []
					# init - building dicts of player points
					for player in allPlayers: 
						# for one player teams it is easy - simply put all the players into the dict.
						team = get_teams_by_players([player])
						if team:
							onePlayerTeams[player.name] = team[0].points
						else:
							onePlayerTeams[player.name] = 0
					if players > 2: 
						# for two player teams all possible combinations need to be investigated.
						teamCombos = list(itertools.combinations(allPlayers, 2))
						for player in teamCombos:
							team = get_teams_by_players([player[0],player[1]])
							teamName = player[0].name + '+' + player[1].name;
							if team:
								twoPlayerTeams[teamName] = team[0].points
							else:
								twoPlayerTeams[teamName] = onePlayerTeams[player[0].name] + onePlayerTeams[player[1].name]
					if players == 6:
						# for three player teams all combinations of three players are proposed, having in mind the previously generated 2 player teams.
						teamCombos = list(itertools.combinations(allPlayers, 3))
						for player in teamCombos:
							team = get_teams_by_players([player[0],player[1],player[2]])
							teamName = player[0].name + '+' + player[1].name + '+' + player[2].name;
							if team:
								threePlayerTeams[teamName] = team[0].points
							else:
								points = twoPlayerTeams[player[0].name + '+' + player[1].name]
								leftOver = 2
								if twoPlayerTeams[player[1].name + '+' + player[2].name] > points:
									points = twoPlayerTeams[player[1].name + '+' + player[2].name]
									leftOver = 0
								if twoPlayerTeams[player[0].name + '+' + player[2].name] > points:
									points = twoPlayerTeams[player[0].name + '+' + player[2].name]
									leftOver = 1
								points += onePlayerTeams[player[leftOver].name]			
								threePlayerTeams[teamName] = points
					if players == 2:
						points = onePlayerTeams
					if players == 4:
						points = twoPlayerTeams
					if players == 6:
						points = threePlayerTeams
					if players == 3: # when there are 3 players, match is 1 vs. 2. So in the points dict there must be both one player and two player teams.
						points = onePlayerTeams
						points.update(twoPlayerTeams)
					combos = list(itertools.combinations(points.keys(), 2)) # making actual matchups by combining all the possible pairs from points
					match = self.makeMatch(combos, points, players) # here the magic happens.
					player1 = combos[match][0] # result team 1
					player2 = combos[match][1] # result team 2
					msg = 'Best Match: ' + player1 + '(' + str(points[player1]) + ') vs. ' + player2 + '(' + str(points[player2]) + ')'
			else:
				error = "Valid number of players: 2, 3, 4, 6"
		else:
			error = "Wrong form data"
		context = {}
		context['msg'] = msg
		context['error'] = error
		context['form'] = self.MakerForm()
		return self.render_to_response(context)
	
	# actual match maker. Determines the best pairings by sum of points in an iterative.
	def makeMatch(self, combos, points, players):
		match = 0
		pts = (max(points.values()) - min(points.values()))*(players-1)
		for i in range(len(combos)):
			combo = combos[i]
			diff = abs(points[combo[0]]-points[combo[1]])
			if diff < pts:
				match = i
				pts = diff
		player1 = combos[match][0]
		player2 = combos[match][1]
		players1 = player1.split('+')
		players2 = player2.split('+')
		if len(players1) + len(players2) <> players:
			del combos[match]
			match = self.makeMatch(combos, points, players)
			player1 = combos[match][0]
			player2 = combos[match][1]
			players1 = player1.split('+')
			players2 = player2.split('+')
		same = 0
		for p1 in players1:
			for p2 in players2:
				if p1 == p2:
					same = 1
					break
			if same:
				break
		if same:
			del combos[match]
			match = self.makeMatch(combos, points, players)
		return match

#################################################################
		
class WeekOverview(TemplateView):
	# overview of all the data for the past week.
	template_name = "overview.html"
		
	def getPoints(sewlf, scores):
		points = {}
		for score in scores:
			if score.home_score > score.away_score:
				points = add(points, score.home.id, 2)
				points = add(points, score.away.id, 0)
			elif score.home_score == score.away_score:
				points = add(points, score.home.id, 1)
				points = add(points, score.away.id, 1)
			else:
				points = add(points, score.home.id, 0)
				points = add(points, score.away.id, 2)
		return points
	
	# getRanks and updateChart are different here due to date interval of a week
	
	def getRanks(self, scores):
		points = self.getPoints(scores)
		games = {}
		for score in scores:
			games = add(games,score.home.id,1)
			games = add(games,score.away.id,1)
		rankDict = []
		for i in range(len(points)):
			team = 0
			pts = -1
			for t, p in points.items():
				if p > pts:
					team = t
					pts = p
				elif p == pts and team!=0 and games[t] < games[team]:
					team = t
					pts = p
			teamObj = Team.objects.get(pk=team)
			rankDict.append({'id': team, 'team': teamObj.name, 'pt': pts, 'games': games[team]}) 
			del points[team]
		return rankDict #returning a dictionary with limitted data instead of full team object
		
	# Updates chart
	def updateChart(self, ranks):
		teams = []
		points = []
		for rank in reversed(ranks):
			teams.append(rank["team"])
			points.append(rank["pt"])
		pos = arange(len(teams))+.5    # the bar centers on the y axis
		figure(1)
		barh(pos, points, align='center')
		yticks(pos, teams)
		xlabel('Points')
		ylabel('Team')
		title('Ranking')
		grid(True)
		savefig("pics/overviewChart.png", dpi=60) # saving into different pic
		clf()
	
	def get_context_data(self, **kwargs):
		context = super(WeekOverview, self).get_context_data(**kwargs)
		start = date.today() + timedelta(weeks=-1) # week limit
		scores = Score.objects.filter(when__gt=start)
		ranks = self.getRanks(scores)
		self.updateChart(ranks)
		context['scores'] = scores
		context['ranks'] = ranks
		context["title"] = 'Week Overview'
		return context
		