from django import forms

class PatentURLForm(forms.Form):
    patent_url = forms.URLField(label='Ссылка на патент', required=True,widget=forms.URLInput(attrs={'class': 'form-control'}))