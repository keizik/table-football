from django import forms
from django.shortcuts import render_to_response
from football.models import Player
from django.views.generic import TemplateView
from functions import get_teams_by_players
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
		context['title'] = "MatchMaker"
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
