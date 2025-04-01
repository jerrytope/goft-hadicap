from django.contrib import admin
from .models import CustomUser, Score, Handicap

class ScoreAdmin(admin.ModelAdmin):
    list_display = ('player', 'course_name', 'score', 'date_played')
    search_fields = ('player__username', 'course_name')
    list_filter = ('date_played',)
    ordering = ('-date_played',)

class HandicapAdmin(admin.ModelAdmin):
    list_display = ('player', 'value')
    search_fields = ('player__username',)
    list_editable = ('value',)  # ✅ Allows direct editing in the admin list view
    ordering = ('value',)

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active', 'is_staff')
    search_fields = ('username', 'email')
    list_filter = ('is_active', 'is_staff')
    ordering = ('username',)
    
    # ✅ Admin can set initial handicap when creating a user
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not Handicap.objects.filter(player=obj).exists():  # Set only if not already set
            Handicap.objects.create(player=obj, value=0.0)  # Default initial handicap

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Score, ScoreAdmin)
admin.site.register(Handicap, HandicapAdmin)
