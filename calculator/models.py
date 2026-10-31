from django.db import models

class Pokemon(models.Model):
    name = models.CharField(max_length=100)
    # New Combat Data
    type1 = models.CharField(max_length=50, default='normal')
    type2 = models.CharField(max_length=50, blank=True, null=True)
    hp = models.IntegerField(default=50)
    attack = models.IntegerField(default=50)
    defense = models.IntegerField(default=50)
    sp_atk = models.IntegerField(default=50)
    sp_def = models.IntegerField(default=50)
    speed = models.IntegerField(default=50)

    def __str__(self):
        return self.name

class HeldItem(models.Model):
    name = models.CharField(max_length=100)
    flat_attack = models.IntegerField(default=0)
    flat_sp_atk = models.IntegerField(default=0)
    flat_defense = models.IntegerField(default=0)
    flat_sp_def = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class Move(models.Model):
    name = models.CharField(max_length=100)
    pokemon = models.ForeignKey(Pokemon, on_delete=models.CASCADE, related_name='moves', null=True, blank=True)
    # New Move Math Data
    move_type = models.CharField(max_length=50, default='normal')
    damage_type = models.CharField(max_length=50, default='physical') # physical, special, or status
    base_damage = models.IntegerField(default=0)
    accuracy = models.IntegerField(default=100)
    scaling_ratio = models.FloatField(default=1.0)

    def __str__(self):
        return self.name

class Team(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    pokemon = models.ForeignKey(Pokemon, on_delete=models.CASCADE)
    held_item = models.ForeignKey(HeldItem, on_delete=models.SET_NULL, null=True, blank=True)
    move1 = models.ForeignKey(Move, on_delete=models.SET_NULL, null=True, blank=True, related_name='move1_set')
    move2 = models.ForeignKey(Move, on_delete=models.SET_NULL, null=True, blank=True, related_name='move2_set')
    move3 = models.ForeignKey(Move, on_delete=models.SET_NULL, null=True, blank=True, related_name='move3_set')
    move4 = models.ForeignKey(Move, on_delete=models.SET_NULL, null=True, blank=True, related_name='move4_set')

    def __str__(self):
        return f"{self.pokemon.name} on {self.team.name}"