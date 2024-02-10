from django import forms

class BasicForm(forms.Form):
    tsv_file = forms.FileField(label='Upload TSV file')

class UploadFileForm(forms.Form):
    file = forms.FileField(label='Select a TSV file')