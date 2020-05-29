from django import forms

from . import models


class PostForm(forms.ModelForm):
    class Meta:
        model = models.Post
        fields = ('body', )

    def clean_body(self):
        data = self.cleaned_data.get('body')
        if len(data) <= 5:
            raise forms.ValidationError("Message is too short")
        return data