from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Score

# ✅ Custom User Registration Form
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ["username", "email", "password1", "password2"]

# ✅ Score Submission Form (ModelForm)
class ScoreForm(forms.ModelForm):
    class Meta:
        model = Score
        fields = ["score"]  # Only score field, player is set in the view

    def __init__(self, *args, **kwargs):
        """
        Optionally receive a 'player' instance to auto-assign.
        """
        self.player = kwargs.pop("player", None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        """
        Override save to assign the player automatically.
        """
        score = super().save(commit=False)
        if self.player:
            score.player = self.player
        if commit:
            score.save()
        return score

class ScoreSubmissionForm(forms.ModelForm):
    class Meta:
        model = Score
        fields = ['course_name', 'score']  # ✅ Ensure 'course_name' is included



from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField()
