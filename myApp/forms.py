from django import forms

class BasicForm(forms.Form):
    tsv_file = forms.FileField(label='Upload TSV file')