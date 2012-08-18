from football.models import Score, Team
from django.views.generic import TemplateView
from datetime import date, timedelta
from pylab import figure, barh, yticks, xlabel, title, grid, savefig, arange, ylabel, clf
from functions import append, add
		
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
		