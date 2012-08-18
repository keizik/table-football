from django.db import models
from django.contrib import admin
	
class Player(models.Model):
	name = models.CharField(max_length=50, unique=True)
	def __unicode__(self):
		return self.name
		
class Team(models.Model):
	name = models.CharField(max_length=200, unique=True, null=True, blank=True)
	players = models.ManyToManyField(Player)
	points = models.IntegerField()
	games = models.IntegerField()
	def __unicode__(self):
		return self.name
	
class Score(models.Model):
	home = models.ForeignKey(Team,related_name="home")
	away = models.ForeignKey(Team,related_name="away")
	home_score = models.IntegerField()
	away_score = models.IntegerField()
	when = models.DateField()

class PlayerAdmin(admin.ModelAdmin):
	list_display = ["name"]
	search_fields = ["name"]
	
class ScoreAdmin(admin.ModelAdmin):
	list_display = ["home", "home_score", "away", "away_score"]
	search_fields = ["home", "away"]
	actions = ["delete"]
	def delete(self, request, queryset):
		# change team data: minus points and games.
		for score in queryset:
			homeTeam = score.home
			awayTeam = score.away
			homeTeam.games = homeTeam.games - 1
			awayTeam.games = awayTeam.games - 1
			if score.home_score > score.away_score:
				homeTeam.points = homeTeam.points - 2
			elif score.home_score < score.away_score:
				awayTeam.points = awayTeam.points - 2
			else:
				homeTeam.points = homeTeam.points - 1
				awayTeam.points = awayTeam.points - 1
			homeTeam.save()
			awayTeam.save()
		queryset.delete()
	delete.short_description = "delete selected"
	def get_actions(self, request):
		actions = super(ScoreAdmin, self).get_actions(request)
		if 'delete_selected' in actions:
			del actions['delete_selected']
		return actions
	
class TeamAdmin(admin.ModelAdmin):
	list_display = ["name", "points"]
	search_fields = ["name"]
	
admin.site.register(Player, PlayerAdmin)
admin.site.register(Score, ScoreAdmin)
admin.site.register(Team, TeamAdmin)