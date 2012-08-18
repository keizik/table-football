from football.models import Score, Team
from django.views.generic import TemplateView
from django.db.models import Q
	
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
