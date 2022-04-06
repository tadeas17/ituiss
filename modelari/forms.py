from django import forms
from django.db.models import fields
from django.forms import Form, ModelForm
from django.forms import widgets
from django.forms.fields import CharField
from django.forms.widgets import Widget
from django.utils import tree
from django.core.files.images import get_image_dimensions
from .models import CompetitionMiniatureCategory, CompetitionType, Miniature, MiniatureRegistration, MiniatureType, Person, User, Competition

from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm, UserChangeForm, UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext, gettext_lazy as _

class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class':'form-control'})
        self.fields['first_name'].widget.attrs.update({'class':'form-control'})
        self.fields['last_name'].widget.attrs.update({'class':'form-control'})
        self.fields['email'].widget.attrs.update({'class':'form-control', 'value':'@'})
        self.fields['password1'].widget.attrs.update({'class':'form-control'})
        self.fields['password2'].widget.attrs.update({'class':'form-control'})


class UserChangeInfo(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
    
    def __init__(self, request, user=None, *args, **kwargs):
        if user is None:
            user = request.user
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class':'form-control'})
        self.fields['username'].error_messages = {}
        self.fields['username'].required = False
        self.fields['username'].help_text = None
        self.fields['username'].disabled = True
        self.fields['username'].initial = user.get_username()
        self.fields['email'].widget.attrs.update({'class':'form-control', 'placeholder': user.email})
        self.fields['first_name'].widget.attrs.update({'class':'form-control', 'placeholder': user.first_name})
        self.fields['last_name'].widget.attrs.update({'class':'form-control', 'placeholder': user.last_name})
        del self.fields['password']


class UserChangePasswordForm(PasswordChangeForm):
    def __init__(self, user, *args, **kwargs) -> None:
        super().__init__(user, *args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class':'form-control'})
        self.fields['new_password1'].widget.attrs.update({'class':'form-control'})
        self.fields['new_password2'].widget.attrs.update({'class':'form-control'})


class UserVerifyPasswordTwiceForm(Form):
    error_messages = {
        'password_incorrect': 'Zadali jste špatné heslo, zkuste prosím znovu.',
        'password_mismatch': _('The two password fields didn’t match.'),
    }

    password1 = forms.CharField(
        label="Heslo",
        strip=False,
        widget=forms.PasswordInput(attrs={'class':'form-control'}),
    )
    password2 = forms.CharField(
        label="Potvrzení hesla",
        widget=forms.PasswordInput(attrs={'class':'form-control'}),
        strip=False,
        help_text="Zadejte znovu stejné heslo, pro ověření.",
    )

    def __init__(self, user, request, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.user = user
        self.request = request

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if not self.user.check_password(password1):
            raise ValidationError(
                self.error_messages['password_incorrect'],
                code='password_incorrect',
            )
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2


class MiniatureForm(ModelForm):
    class Meta:
        model = Miniature
        fields = (
            'name',
            'miniature_type',
            'scale',
            'manufacturer'
        )

    def __init__(self, miniature=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['name'].widget.attrs.update({'class':'form-control'})
        self.fields['scale'].widget.attrs.update({'class':'form-control'})
        self.fields['manufacturer'].widget.attrs.update({'class':'form-control'})
        self.fields['miniature_type'].widget.attrs.update({'class':"form-select"})

        if miniature is not None:
            self.initial['name'] = miniature.name
            self.initial['scale'] = miniature.scale
            self.initial['manufacturer'] = miniature.manufacturer
            self.initial['miniature_type'] = miniature.miniature_type


class PersonCreationForm(ModelForm):
    class Meta:
        model = Person
        fields = (
            'first_name',
            'last_name',
            'town',
            'address',
            'email',
            'phone',
            'country'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['town'].widget.attrs.update({'class':'form-control'})
        self.fields['first_name'].widget.attrs.update({'class':'form-control'})
        self.fields['last_name'].widget.attrs.update({'class':'form-control'})

        self.fields['email'].required = False
        self.fields['address'].required = False
        self.fields['phone'].required = False
        self.fields['country'].required = False
        self.fields['email'].widget.attrs.update({'class':'form-control'})
        self.fields['country'].widget.attrs.update({'class':'form-control'})
        self.fields['address'].widget.attrs.update({'class':'form-control'})
        self.fields['phone'].widget.attrs.update({'class':'form-control'})


class PersonDisplayForm(PersonCreationForm):
    def __init__(self, person, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.person = person
        self.fields['email'].disabled = True
        self.fields['email'].initial = person.email
        self.fields['last_name'].initial = person.last_name
        self.fields['first_name'].disabled = True
        self.fields['first_name'].initial = person.first_name
        self.fields['last_name'].disabled = True
        self.fields['address'].disabled = True
        self.fields['phone'].disabled = True
        self.fields['country'].disabled = True
        self.fields['address'].initial = person.address
        self.fields['phone'].initial = person.phone
        self.fields['country'].initial = person.country
        self.fields['town'].disabled = True
        self.fields['town'].initial = person.town


class UserLoginForms(AuthenticationForm):
    next = "/"

    class Meta:
        model = User
        fields = ('username', 'password')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class':'form-control'})
        self.fields['password'].widget.attrs.update({'class':'form-control'})


class CompetitionForm(ModelForm):
    error_messages = {
        'date_reg_vs_org': 'Doba registrace nesmí být později než pořádání.',
        'big_resolution_logo': 'Logo soutěže nesmí mít rozlišení větší než 300*300 pixelů.'
    }

    class Meta:
        model = Competition
        fields = ('name',
                  'type',
                  'date_organisation',
                  'date_registration',
                  'description',
                  'competition_logo',
                  'visibly',
                  'organizer',
                  )

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'date_organisation': forms.DateTimeInput(attrs={'class': 'form-control'}, format='%Y/%m/%d %H:%M'),
            'date_registration': forms.DateTimeInput(attrs={'class': 'form-control'}, format='%Y/%m/%d %H:%M'),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'competition_logo': forms.FileInput(attrs={'class': 'form-control'}),
            'organizer': forms.Select(attrs={'class': 'form-control'}),
            'visibly': forms.CheckboxInput(attrs={'checked': ''}),
        }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['type'].required = False
            self.fields['date_organisation'].required = False
            self.fields['date_registration'].required = False
            self.fields['description'].required = False
            self.fields['competition_logo'].required = False
            self.fields['organizer'].required = True

        def is_valid(self):
            validation_response = super(CompetitionForm, self).is_valid()
            if not validation_response:
                return validation_response

            if 'date_registration' in self.cleaned_data.keys() and self.cleaned_data['date_registration'] is not None:
                if self.cleaned_data['date_registration'] < self.cleaned_data['date_organisation']:
                    raise ValidationError(
                        self.error_messages['date_reg_vs_org'],
                        code='date_reg_vs_org',
                    )
            # competition_logo = self.cleaned_data['competition_logo']
            # if competition_logo:
            #     w, h = get_image_dimensions(competition_logo)
            #     if w > 300 or h > 300:
            #         raise ValidationError(
            #             self.error_messages['big_resolution_logo'],
            #             code='big_resolution_logo',
            #         )
            return True


class CompetitionDisplayForm(CompetitionForm):

    def __init__(self, competition, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.competition = competition
        self.fields['name'].disabled = True
        self.fields['name'].initial = competition.name
        self.fields['type'].disabled = True
        self.fields['type'].initial = competition.type
        self.fields['date_organisation'].disabled = True
        self.fields['date_organisation'].initial = competition.date_organisation
        self.fields['date_registration'].disabled = True
        self.fields['date_registration'].initial = competition.date_registration
        self.fields['description'].disabled = True
        self.fields['description'].initial = competition.description
        self.fields['competition_logo'].widget = forms.HiddenInput()
        self.fields['competition_logo'].disabled = True
        self.fields['competition_logo'].initial = competition.competition_logo
        self.fields['visibly'].disabled = True
        self.fields['visibly'].initial = competition.visibly
        self.fields['organizer'].widget = forms.TextInput(attrs={'class': 'form-control'})
        self.fields['organizer'].disabled = True
        self.fields['organizer'].initial = "{} {}".format(competition.organizer.first_name, competition.organizer.last_name)


class CompetitionUpdateForm(CompetitionForm):

    def __init__(self, competition, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.competition = competition
        self.fields['name'].initial = competition.name
        self.fields['type'].initial = competition.type
        self.fields['date_organisation'].initial = competition.date_organisation
        self.fields['date_registration'].initial = competition.date_registration
        self.fields['description'].initial = competition.description
        self.fields['competition_logo'].initial = competition.competition_logo
        #self.fields['organizer'].widget = forms.TextInput(attrs={'class': 'form-control'})
        #self.fields['organizer'].disabled = True
        #self.fields['organizer'].initial = "{} {}".format(competition.organizer.first_name,
        #                                                  competition.organizer.last_name)
        self.fields['visibly'].initial = competition.visibly


class CompetitionCreateForm(CompetitionForm):

    def is_valid(self):
        super(CompetitionCreateForm, self).is_valid()


class MiniatureTypeForm(ModelForm):
    class Meta:
        model = MiniatureType
        fields = ('name',)

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }


class MiniatureRegistrationForm(ModelForm):
    class Meta:
        model = MiniatureRegistration
        fields = (
            'miniature',
            'category',
            'additional_information',
            'competition'
        )

        widgets = {
            'miniature': forms.HiddenInput(),
            'additional_information': forms.Textarea(attrs={'class': 'form-control'}),
            'competition': forms.HiddenInput(),
            'category': forms.Select(attrs={'class': 'form-control'})
        }
    
    def __init__(self, competition_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['category'].queryset = CompetitionMiniatureCategory.objects.filter(competition=competition_id)
        self.fields['additional_information'].required = False


class CompetitionTypeForm(ModelForm):
    class Meta:
        model = CompetitionType
        fields = ('name',)

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }


class CompetitionMiniatureCategoryForm(ModelForm):
    class Meta:
        model = CompetitionMiniatureCategory
        fields = ('name', 'competition')

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'competition': forms.HiddenInput()
        }


class CompetitionMiniatureCategoryListForm(CompetitionMiniatureCategoryForm):

    def __init__(self, competition_miniature_category):
        super(CompetitionMiniatureCategory, self).__init__()
        self.fields['name'].disabled = True
        self.fields['name'].initial = competition_miniature_category.name
