from django import forms


class UploadFileForm(forms.Form):
    file = forms.FileField()
    granularity = forms.ChoiceField(choices=[
        ('raw', 'raw'), ('hour', 'hour'), ('day', 'day'),
        ('week', 'week'), ('month', 'month'), ('year', 'year')])
    search_string = forms.ChoiceField(choices=[
        ('full', 'full'), ('words', 'words')])
