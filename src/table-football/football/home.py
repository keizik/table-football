from django import forms
from django.shortcuts import render_to_response
from django.template import RequestContext
from football.models import Score, Player, Team
from django.views.generic import TemplateView
from datetime import date
from pylab import figure, barh, yticks, xlabel, title, grid, savefig, arange, ylabel, clf
from functions import append, getRanks, get_teams_by_players

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
		self.updateChart(ranks) #updating chart
		
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
