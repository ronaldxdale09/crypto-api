from django import forms

class BaseModelForm(forms.ModelForm):
    """
    A base form with common validation and styling enhancements.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling or attributes to all fields
        for field_name, field in self.fields.items():
            if isinstance(field, forms.CharField) and not isinstance(field, forms.PasswordInput):
                field.widget.attrs.update({'class': 'form-control'})
                
    def clean(self):
        """Common validation that applies to all forms"""
        cleaned_data = super().clean()
        return cleaned_data