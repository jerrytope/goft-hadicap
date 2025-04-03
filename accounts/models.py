
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# ✅ Custom User Model
class CustomUser(AbstractUser):
    is_player = models.BooleanField(default=True)  # Players by default
    is_admin = models.BooleanField(default=False)  # Admins can be assigned manually
    handicap = models.OneToOneField("Handicap", on_delete=models.SET_NULL, null=True, blank=True, related_name="user_handicap")

    def save(self, *args, **kwargs):
        """Ensure every new player gets a default handicap"""
        is_new = self._state.adding  # ✅ Check if new user
        super().save(*args, **kwargs)  # ✅ Save user first

        if is_new and self.is_player and self.handicap is None:
            # ✅ Create handicap only if it doesn't already exist
            handicap = Handicap.objects.create(player=self, value=28.0)
            CustomUser.objects.filter(pk=self.pk).update(handicap=handicap)  # ✅ Assign and save

        # ✅ Refresh instance to ensure the new handicap is reflected
        self.refresh_from_db()


# ✅ Score Model
class Score(models.Model):
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course_name = models.CharField(max_length=255)  # ✅ Add this field
    score = models.IntegerField()
    date_played = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return f"{self.player.username} - {self.score}"


# ✅ Handicap Model
class Handicap(models.Model):
    player = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # ✅ Avoid circular import issues
        on_delete=models.CASCADE,
        related_name="player_handicap"
    )
    value = models.FloatField(default=28.0)

    @staticmethod
    def update_handicap(player, new_score):
        """
        Updates the player's handicap based on their score.
        """
        COURSE_PAR = 72  # ✅ Official course par

        # ✅ Get Player Handicap Instance
        handicap, created = Handicap.objects.get_or_create(player=player)
        current_hcp = handicap.value

        # ✅ Determine Category and Threshold
        if 1 <= current_hcp <= 5:
            threshold = 72  # Category 1
            factor = 0.1
        elif 6 <= current_hcp <= 12:
            threshold = 73  # Category 2
            factor = 0.2
        elif 13 <= current_hcp <= 18:
            threshold = 75  # Category 3
            factor = 0.3
        else:
            threshold = 76  # Category 4
            factor = 0.4

        # ✅ Correctly Calculate New Handicap
        if COURSE_PAR <= new_score <= threshold:
            new_hcp = current_hcp  # ✅ No change within threshold
        elif new_score > threshold:
            new_hcp = current_hcp + 0.1  # ✅ Add +0.1 if above threshold
        else:
            difference = COURSE_PAR - new_score
            new_hcp = current_hcp - (factor * difference)  # ✅ Reduce handicap

        new_hcp = round(new_hcp, 2)  # ✅ Round to 2 decimal places

        # ✅ Ensure Handicap Limits
        new_hcp = min(new_hcp, 28)  # Max 28
        new_hcp = max(new_hcp, 0)   # Min 0

        # ✅ Save New Handicap Value
        handicap.value = new_hcp
        handicap.save(update_fields=["value"])

        return new_hcp  # ✅ Return updated value

    def __str__(self):
        return f"{self.player.username} - Handicap: {self.value}"
