from typing import Container
from django.conf.urls import handler403
from django.db.models.aggregates import Min
from django.http import response
from django.http.response import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.generic import View, CreateView
from django.template import context, loader
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string

from datetime import datetime, tzinfo, date, timedelta

#Ať je tu uklizeno v těch importech! Stačí, že mám bordel v pokoji.
from .forms import MiniatureForm, MiniatureRegistrationForm, PersonCreationForm, PersonDisplayForm, UserChangeInfo, \
    UserForm, UserLoginForms, \
    UserChangePasswordForm, UserVerifyPasswordTwiceForm, CompetitionCreateForm, CompetitionDisplayForm, \
    CompetitionUpdateForm, MiniatureTypeForm, CompetitionTypeForm, CompetitionForm, CompetitionMiniatureCategoryForm
from .models import CompetitionMiniatureCategory, Miniature, Person, Competition, MiniatureType, CompetitionType, MiniatureRegistration
from django.contrib.auth.models import User


def handler404(request, exception, template_name="404.html"):
    response = render(context={'exception': exception}, template_name=template_name)
    response.status_code = 404
    return response


class PersonMiniaturesView(View):
    def get(self, request, person_id=None, *args, **kwargs):
        person = Person.objects.filter(id=person_id).first()
        if person is None:
            return HttpResponseRedirect("/persons")
        miniatures = Miniature.objects.filter(owner=person).order_by('id')
        miniature_list = []
        for miniature in miniatures:
            miniature_list.append([miniature, MiniatureForm(miniature=miniature, auto_id=f"{miniature.id}_%s")])
        if person.owner == request.user or request.user.is_superuser:
            form1 = MiniatureForm()
            return render(request, 'persons/miniature_view.html', {'form1':form1, 'person':person, 'miniature_list':miniature_list})

    def add_miniature(self, request, person_id, *args, **kwargs):
        form = MiniatureForm(data=request.POST)
        if not form.is_valid():
            #TODO
            response = JsonResponse({"error":"Invalid form"})
            response.status_code = 403
            return response

        miniature = Miniature(
            owner = Person.objects.get(pk=request.POST['form_person_id']),
            miniature_type = form.cleaned_data['miniature_type'],
            name = form.cleaned_data['name'],
            scale = form.cleaned_data['scale'],
            manufacturer = form.cleaned_data['manufacturer'],
        )
        miniature.save()

        form = MiniatureForm(miniature=miniature, data=request.POST, auto_id=f"{miniature.id}_%s")

        html = render_to_string('persons/miniature_item.html', {'miniature': miniature, 'form': form})
        return HttpResponse(html)
    
    def edit_miniature(self, request, person_id, *args, **kwargs):
        if Miniature.objects.filter(pk=request.POST['form_miniature_id']).exists():
            form = MiniatureForm(data=request.POST, instance=Miniature.objects.get(id=request.POST['form_miniature_id']))
            if form.is_valid():
                miniature = form.save() #TODO otestovat
                form = MiniatureForm(miniature=miniature, data=request.POST, auto_id=f"{miniature.id}_%s")
                html = render_to_string('persons/miniature_item.html', {'miniature': miniature, 'form': form})
                return HttpResponse(html)
            else:
                miniature = Miniature.objects.get(id=request.POST['form_miniature_id'])
                form = MiniatureForm(miniature=miniature, data=request.POST, auto_id=f"{miniature.id}_%s")
                form.is_valid()
                html = render_to_string('persons/miniature_item.html', {'miniature': miniature, 'form': form, 'errors': True})
                return HttpResponse(html)
        else:
            response = JsonResponse({'error': 'Miniature does not exist'})
            response.status_code = 404
            return response

    def post(self, request, person_id=None, *args, **kwargs):
        if request.POST.get('request') == 'add_miniature':
            return self.add_miniature(request, person_id, *args, **kwargs)

        if request.POST.get('request') == 'edit_miniature':
            return self.edit_miniature(request, person_id, *args, **kwargs)

        if request.POST.get('request') == 'delete_miniature':
            miniature = Miniature.objects.get(id=request.POST['miniature_id'])
            if miniature.owner.owner != request.user and not request.user.is_superuser:
                response = JsonResponse({'error': 'User is not the miniature owner'})
                response.status_code = 403
                return response

            return JsonResponse({"success":True})

class PersonView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            HttpResponseRedirect("/")

        if 'get_miniature' in request.GET:
            person = Person.objects.all().first()
            
            person_data = {
                "first_name":person.first_name,
                "last_name":person.last_name
            }
            return JsonResponse(person_data, safe=False)
        context = {}
        template_name = "persons/persons.html"
        if request.user.is_superuser:
            persons = Person.objects.all().order_by('last_name')
        else:
            persons = Person.objects.filter(owner=request.user).order_by('last_name')
        context['persons'] = []
        context['forms'] = []
        for person in persons:
            miniature_count = Miniature.objects.filter(owner=person).count()
            context['persons'].append([person, miniature_count, PersonCreationForm(instance=person)])
        context['form'] = PersonCreationForm()
        
        return render(request, template_name=template_name, context=context)

    def delete_person(self, request):
        if Person.objects.filter(id=request.POST.get('person_id')).exists():
            if Person.objects.get(id=request.POST['person_id']).owner == request.user:
                Person.objects.filter(id=request.POST['person_id']).delete()
                return JsonResponse({'success':'true'})
            else:
                response = JsonResponse({'error':"User not the owner of the person"})
                response.status_code = 403
                return response

        response = JsonResponse({'error':"Couldn't find the given person"})
        response.status_code = 403
        return response

    def add_person(self, request):
        form = PersonCreationForm(data=request.POST)
        if form.is_valid():
            person = form.save()
            person.owner = request.user
            person.save()
            form = PersonCreationForm(instance=person)
            html = render_to_string('persons/person_card.html', {'user': request.user,'person': person, 'count': Miniature.objects.filter(owner=person).count(), 'form': form})
            return HttpResponse(html)
        else:
            html = render_to_string('persons/person_form.html', {'form': form})
            response = HttpResponse(html)
            #response.status_code = 403
            return response

    def edit_person(self, request):
        person = Person.objects.filter(id=request.POST.get('person_id'))
        if not person.exists():
            response = JsonResponse({'error': 'Person does not exist'})
            response.status_code = 404
            return response

        person = person.first()
        if person.owner != request.user and not request.user.is_superuser:
            response = JsonResponse({'error': 'Not the person owner'})
            response.status_code = 403
            return response

        form = PersonCreationForm(instance=person, data=request.POST)
        if form.is_valid():
            person = form.save()

            count = Miniature.objects.filter(owner=person).count()
            html = render_to_string('persons/person_card_content.html', {'person': person, 'count': count}, request)
            return JsonResponse({'status':'success', 'data':html})
        else:
            html = render_to_string('persons/person_card_form.html', {'form': form}, request)
            return JsonResponse({'status': 'invalid_form', 'form': html})

    def post(self, request, *args, **kwargs):
        if request.POST.get('request') == 'edit_person':
            return self.edit_person(request)
        if request.POST.get('request') == 'delete_person':
            return self.delete_person(request)
        if request.POST.get('request') == 'add_person':
            return self.add_person(request)

        return HttpResponseRedirect("/persons")

class UsersView(View):
    def deactivate_user(self, request):
        if User.objects.filter(username=request.GET['deactivate']).exists():
            user = User.objects.get(username=request.GET['deactivate'])
            if user is not None and not user.is_superuser:
                user.is_active = False
                user.save()

    def activate_user(self, request):
        if User.objects.filter(username=request.GET['activate']).exists():
            user = User.objects.get(username=request.GET['activate'])
            if user is not None and not user.is_superuser:
                user.is_active = True
                user.save()

    def edit_user(self, request):
        if not User.objects.filter(username=request.GET['edit']).exists():
            return HttpResponseRedirect("/users")
        user = User.objects.get(username=request.GET['edit'])
        if user.is_superuser:
            return HttpResponseRedirect("/users")
        form1 = UserChangeInfo(data=request.POST, request=request, user=user)
        del form1.errors['username']
        context = {'form1':form1, 'username':user.get_username()}
        return render(request, 'admin/user_detail.html', context)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return HttpResponseRedirect("/")
        else:
            if 'deactivate' in request.GET:
                self.deactivate_user(request)
            if 'activate' in request.GET:
                self.activate_user(request)
            if 'edit' in request.GET:
                return self.edit_user(request)
            
            active_users = User.objects.filter(is_active=True)
            inactive_users = User.objects.filter(is_active=False)
            return render(request, 'admin/users.html', {'active_users':active_users, 'inactive_users':inactive_users})
        
    def post(self, request, *args, **kwargs):
        return HttpResponseRedirect("/users")

class LoginPageView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            request.session["login_error"] = True
            return HttpResponseRedirect("/")
        template_name = 'accounts/login.html'
        form = UserLoginForms()
        context = {
            'form': form
        }        
        if 'login_result' in request.session.keys():
            context['login_error'] = True
            del request.session['login_result']
        return render(request, template_name=template_name, context=context)        

    def post(self, request, *args, **kwargs):
        template_name = 'accounts/login.html'
        form = UserLoginForms(data=request.POST)
        if form.is_valid():
            pass
        else:
            user = form.get_user()

            if not User.objects.filter(username=form.cleaned_data.get('username')).exists():
                form.add_error('username', 'Daný uživatel neexistuje.')
            else:
                form.add_error('password', 'Nesprávné heslo.')
            return render(request, template_name=template_name, context={'form':form})

        user = authenticate(
            request,
            username=form.cleaned_data.get('username'),
            password=form.cleaned_data.get('password'))
        if user is not None:
            login(request, user)
            # Redirect to a success page.
            request.session['login_success'] = True #success
            if 'redirect_page' in request.GET.keys():
                return HttpResponseRedirect("/{}".format(request.GET['redirect_page']))
            return HttpResponseRedirect("/")
        else:
            if User.objects.filter(username=form.cleaned_data.get('username')).exists():
                form.add_error('username', 'Daný uživatel neexistuje.')
            else:
                form.add_error('password', 'Nesprávné heslo.')
            return render(request, template_name=template_name, context={'form':form})


class RegistrationPageView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            request.session["registration_error"] = True
            return HttpResponseRedirect("/")

        context = {}
        if 'registration_success' in request.session.keys():
            context['registration_error'] = True
            del request.session['registration_success']
        form = UserForm()
        context['form'] = form
        return render(request, 'accounts/registration.html', context)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            form = UserForm(data=request.POST)
            if form.is_valid():
                user = form.save()

                login(request, user, None)
                request.session['registration_success'] = True
                return HttpResponseRedirect("/")
            else:
                return render(request, 'accounts/registration.html',{'form':form})
        else:
            return HttpResponseRedirect("/")


class LogoutPageView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
        request.session['logout_success'] = True
        return HttpResponseRedirect("/")

class AccountView(View):
    def get(self, request, *args, **kwargs):
        form1 = UserChangeInfo(data=request.POST, request=request)
        form2 = UserChangePasswordForm(request.user)
        form3 = UserVerifyPasswordTwiceForm(request.user, request)
        del form1.errors['username']
        context = {
            'form2':form2,
            'form1':form1,
            'form3':form3
        }
        if 'change_success' in request.session:
            context['change_success'] = request.session['change_success']
            del request.session['change_success']

        return render(request, 'accounts/overview.html', context)
    
    def post(self, request, *args, **kwargs):
        form1 = UserChangeInfo(data=request.POST, request=request)
        form2 = UserChangePasswordForm(request.user, data=request.POST)
        form3 = UserVerifyPasswordTwiceForm(request.user, request, data=request.POST)
        if 'button1' in request.POST:
            form2.errors.clear()
            del form1.errors['username']
            
            if form1.is_valid():
                user = User.objects.get(username=request.user.get_username())
                if 'first_name' in form1.changed_data:
                    user.first_name = form1.cleaned_data.get('first_name')
                if 'last_name' in form1.changed_data:
                    user.last_name = form1.cleaned_data.get('last_name')
                if 'email' in form1.changed_data:
                    user.email = form1.cleaned_data.get('email')
                user.save()
                if len(form1.changed_data) != 0:
                    request.session['change_success'] = 'Údaje úspěšně změněny'
            else:
                return render(request, 'accounts/overview.html', {'form3':form3, 'form2':form2, 'form1':form1})
        elif 'button2' in request.POST:
            form1.errors.clear()
            if form2.is_valid():

                user = User.objects.get(username=request.user.get_username())
                user.set_password(form2.cleaned_data.get('new_password1'))
                user.save()
                login(request, user)
                request.session['change_success'] = 'Heslo úspěšně změněno'
            else:
                return render(request, 'accounts/overview.html', {'form3':form3, 'form2':form2, 'form1':form1})
        elif 'button3' in request.POST:
            form1.errors.clear()
            form2.errors.clear()
            if form3.is_valid():
                user = User.objects.get(username=request.user.get_username())
                user.is_active = False
                user.save()
                logout(request)
                request.session['delete_account'] = "Účet úspěšně smazán."
                return HttpResponseRedirect("/")
            else:
                return render(request, 'accounts/overview.html', {'form3':form3, 'form2':form2, 'form1':form1})

        return HttpResponseRedirect("/account")
        

class HomePageView(View):
    def get(self, request, *args, **kwargs):
        template_name = 'home_page.html'
        context = {
            'registration_error':False
        }
        if 'registration_error' in request.session.keys():
            context['registration_error'] = True
            del request.session['registration_error']
        if 'registration_success' in request.session.keys():
            context['registration_success'] = request.session['registration_success']
            del request.session['registration_success']
        if 'login_success' in request.session.keys():
            context['login_success'] = True
            del request.session['login_success']
        if 'logout_success' in request.session.keys():
            context['logout_success'] = True
            del request.session['logout_success']
        if 'delete_account' in request.session.keys():
            context['delete_account'] = request.session['delete_account']
            del request.session['delete_account']

        return render(request, template_name=template_name, context=context)


class CompetitionEditView(View):

    def get(self, request, competition_id=None, *args, **kwargs):
        template_name = 'competitions/competition_detail.html'
        context = {}

        if competition_id is None:
            return HttpResponseRedirect('/competitions')

        try:
            competition_model = Competition.objects.get(pk=competition_id)
        except Competition.DoesNotExist:
            return HttpResponseRedirect('/competitions')

        if request.user.is_authenticated and request.user.id == competition_model.organizer.id:
            form_class = CompetitionUpdateForm(competition=competition_model)
            context['submit_btn'] = True
        else:
            form_class = CompetitionDisplayForm(competition=competition_model)
            context['submit_btn'] = False

        context['form'] = form_class
        return render(request, template_name, context)

    def post(self, request, competition_id=None, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect('/login?redirect_page=competitions')

        if competition_id is None:
            return HttpResponseRedirect('/competitions')

        try:
            competition_model = Competition.objects.get(pk=competition_id)
        except Competition.DoesNotExist:
            return HttpResponseRedirect('/competitions')

        if not(request.user.is_authenticated and request.user.id == competition_model.id):
            pass
        #TODO ????????????? 

        template_name = 'competitions/competition_detail.html'
        data = request.POST.copy()
        data['date_organisation'] = data['date_organisation'].replace("/", "-")
        data['date_registration'] = data['date_registration'].replace("/", "-")
        data['organizer'] = request.user.id

        form = CompetitionCreateForm(data, request.FILES, instance=competition_model)
        context = {'form': form}

        if form.is_valid():
            form.save()
            return HttpResponseRedirect("/competition/{}".format(competition_id))

        return render(request, template_name, context)


class CompetitionCreateView(View):

    #success_url = '/success/'
    def get(self, request, *args, **kwargs):
        template_name = 'competitions/competition_create.html'
        form_class = CompetitionCreateForm
        context = {}

        if not request.user.is_authenticated:
            return HttpResponseRedirect('/login?redirect_page=competition-create')

        context['form'] = form_class
        return render(request, template_name, context)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return HttpResponseRedirect('/competitions')

        template_name = 'competitions/competition_create.html'
        data = request.POST.copy()
        if 'date_organisation' in data:
            data['date_organisation'] = data['date_organisation'].replace("/", "-")
        if 'date_registration' in data:
            data['date_registration'] = data['date_registration'].replace("/", "-")
        #data['organizer'] = request.user.id

        form = CompetitionForm(data, request.FILES)
        context = {'form': form}

        if form.is_valid():
            competition = form.save()
            return HttpResponseRedirect("/competition/{}".format(competition.id))

        return render(request, template_name, context)


class CategoriesView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseRedirect("/")

        miniature_types_tmp = MiniatureType.objects.all()
        competition_types_tmp = CompetitionType.objects.all()
        miniature_types = []
        competition_types = []
        for miniature_type in miniature_types_tmp:
            miniature_types.append([miniature_type, Miniature.objects.filter(miniature_type=miniature_type).count()])
        for competition_type in competition_types_tmp:
            competition_types.append([competition_type, Competition.objects.filter(type=competition_type).count()])
        miniature_type_form = MiniatureTypeForm(auto_id="miniature_%s")
        competition_type_form = CompetitionTypeForm(auto_id="competition_%s")

        return render(
            request,
            'admin/categories.html',
            {
                'miniature_types': miniature_types,
                'competition_types': competition_types,
                'miniature_type_form': miniature_type_form,
                'competition_type_form': competition_type_form})

    def add_miniature_type(self, request):
        if 'miniature_type' not in request.POST:
            response = JsonResponse({'error': 'Required request data missing'})
            response.status_code = 403
            return response

        miniature_type = MiniatureType.objects.create(name=request.POST.get('miniature_type'))
        try:
            miniature_type.save()
        except Exception as e:
            response = JsonResponse({'error': 'Miniature type already exists'})
            response.status_code = 403
            return response

        html = render_to_string('admin/miniature_category_row.html', {'type': miniature_type, 'count': 0})
        return HttpResponse(html)


    def add_competition_type(self, request):
        if 'competition_type' not in request.POST:
            response = JsonResponse({'error': 'Required request data missing'})
            response.status_code = 403
            return response

        competition_type = CompetitionType.objects.create(name=request.POST.get('competition_type'))
        try:
            competition_type.save()
        except Exception as e:
            response = JsonResponse({'error': 'Competition type already exists'})
            response.status_code = 403
            return response

        html = render_to_string('admin/competition_category_row.html', {'type': competition_type, 'count': 0})
        return HttpResponse(html)


    def delete_miniature_type(self, request):
        if 'miniature_type_id' not in request.POST:
            response = JsonResponse({'error': 'Required request data missing'})
            response.status_code = 403
            return response

        MiniatureType.objects.filter(id=request.POST.get('miniature_type_id')).delete()
        return JsonResponse({'success': 'true'})

    def delete_competition_type(self, request):
        if 'competition_type_id' not in request.POST:
            response = JsonResponse({'error': 'Required request data missing'})
            response.status_code = 403
            return response

        CompetitionType.objects.filter(id=request.POST.get('competition_type_id')).delete()
        return JsonResponse({'success': 'true'})


    def post(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            response = JsonResponse({'error': 'User is not superuser'})
            response.status_code = 403
            return response

        if request.POST.get('request') == 'add_miniature_type':
            return self.add_miniature_type(request)
        if request.POST.get('request') == 'delete_miniature_type':
            return self.delete_miniature_type(request)
        if request.POST.get('request') == 'add_competition_type':
            return self.add_competition_type(request)
        if request.POST.get('request') == 'delete_competition_type':
            return self.delete_competition_type(request)

class CompetitionOverviewView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            upcoming_competitions = Competition.objects.filter(date_organisation__gte = date.today()).order_by('date_organisation')
            past_competitions = Competition.objects.filter(date_organisation__lt = date.today() ).order_by('-date_organisation')
            dateless_competitions = Competition.objects.filter(date_organisation=None)
            return render(request, 'competitions/competitions_overview.html', {
                'upcoming_competitions':upcoming_competitions,
                'past_competitions': past_competitions,
                'dateless_competitions': dateless_competitions
            })
        elif request.user.is_anonymous:
            upcoming_competitions = Competition.objects.filter(visibly=True, date_organisation__gte = date.today()).order_by('date_organisation')
            past_competitions = Competition.objects.filter(visibly=True, date_organisation__lt = date.today() ).order_by('-date_organisation')
            return render(request, 'competitions/competitions_overview.html', {
                'upcoming_competitions':upcoming_competitions,
                'past_competitions': past_competitions
            })
        else:
            upcoming_competitions = Competition.objects.filter(Q(visibly=True) | Q(organizer=request.user), date_organisation__gte = date.today() ).order_by('date_organisation')
            past_competitions = Competition.objects.filter(Q(visibly=True) | Q(organizer=request.user), date_organisation__lt = date.today()).order_by('-date_organisation')
            my_competitions = Competition.objects.filter(organizer=request.user)    
            return render(request, 'competitions/competitions_overview.html', {
                'upcoming_competitions':upcoming_competitions,
                'past_competitions': past_competitions,
                'my_competitions': my_competitions
            })

class CompetitionDetailView(View):
    def get(self, request, *args, **kwargs):
        competition_id = kwargs.get('competition_id')
        competition = Competition.objects.filter(id=competition_id).first()
        if competition is None:
            return HttpResponseRedirect("/competitions")

        form = CompetitionUpdateForm(competition=competition, instance=competition)

        return render(request, 'competitions/competition_detail.html', {'competition': competition, 'form': form})

    def post(self, request, *args, **kwargs):
        competition_id = kwargs.get('competition_id')

        if request.POST.get('request') == 'delete_competition':
            if not request.user.is_superuser:
                return HttpResponseRedirect("")
            
            Competition.objects.filter(id=competition_id).delete()
            return HttpResponseRedirect("/competitions")


        if request.POST.get('request') == 'change_visibility':
            competition = Competition.objects.filter(id=competition_id).first()
            if competition is None:
                response = JsonResponse({'error':'Competition does not exist'})
                response.status_code = 404
                return response
            if competition.organizer != request.user and not request.user.is_superuser:
                response = JsonResponse({'error': 'Not the owner of the competition'})
                response.status_code = 403
                return response

            competition.visibly = not competition.visibly
            competition.save()
            if competition.visibly:
                return JsonResponse({'status': 'visible'})
            else:
                return JsonResponse({'status': 'invisible'})

        competition = Competition.objects.get(id=competition_id)
        if competition.organizer != request.user and not request.user.is_superuser:
            response = JsonResponse({'error': 'Not the owner of the competition'})
            response.status_code = 403
            return response

        data = request.POST.copy()
        data['date_organisation'] = data['date_organisation'].replace("/", "-")
        data['date_registration'] = data['date_registration'].replace("/", "-")
        if data.get('organizer') is None:
            data['organizer'] = request.user

        form = CompetitionUpdateForm(instance=competition, data=data, competition=competition, files=request.FILES if request.FILES.get('competition_logo') is not None else None)
        if form.is_valid():
            competition = form.save()

            return JsonResponse(
                {
                    'status': 'success',
                    'name': competition.name,
                    'type': competition.type.name if competition.type is not None else None,
                    # Aby se zachoval formát v html, tak se to musí vyrenderovat znova...
                    'description': render_to_string('competitions/competition_description.html', {'description': competition.description}),
                    'date_organisation': render_to_string('competitions/competition_datetime.html', {'date':competition.date_organisation}),
                    'date_registration': render_to_string('competitions/competition_datetime.html', {'date':competition.date_registration}),
                    'competition_logo': competition.competition_logo.url if competition.competition_logo else None,
                    'visibly': competition.visibly,
                    'organizer': render_to_string('competitions/competition_organizer.html', {'organizer': competition.organizer})
                }
            )
        else:
            return JsonResponse(
                {
                    'status': 'form_invalid',
                    'form': render_to_string('competitions/competition_edit_form.html', {'form': form}, request)
                }
            )

class CompetitionRegistrationView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/competitions")

        competition_id = kwargs.get('competition_id')
        form = MiniatureRegistrationForm(competition_id=competition_id)
        persons = Person.objects.filter(owner=request.user)
        persons_with_miniatures = []
        for person in persons:
            miniatures = Miniature.objects.filter(owner=person)
            miniatures_list = []
            for miniature in miniatures:
                if MiniatureRegistration.objects.filter(competition=competition_id, miniature=miniature.id).exists():
                    miniatures_list.append([miniature, True])
                else:
                    miniatures_list.append([miniature, False])
            persons_with_miniatures.append([person, miniatures_list])

        return render(request, 'competitions/competition_registration.html', {'form': form, 'persons': persons_with_miniatures, 'competition_id':competition_id})

    def post(self, request, *args, **kwargs):
        competition_id = kwargs.get('competition_id')
        if request.POST.get('request') == 'fill_form':
            if MiniatureRegistration.objects.filter(competition=competition_id, miniature=request.POST.get('miniature_id')).exists():
                miniature_registration = MiniatureRegistration.objects.get(competition=competition_id, miniature=request.POST.get('miniature_id'))
                return JsonResponse({
                    'status': 'existing',
                    'category':miniature_registration.category.id,
                    'additional_information': miniature_registration.additional_information
                })
            else:
                return JsonResponse({'status': 'uncreated'})
        if request.POST.get('request') == 'unregister':
            if MiniatureRegistration.objects.filter(competition=competition_id, miniature=request.POST.get('miniature_id')).exists():
                if Competition.objects.get(id=competition_id).date_registration < datetime.now().astimezone():
                    return JsonResponse({'error': "Cannot make changes to registration after registration deadline", 'status': 'reg_deadline'})
                MiniatureRegistration.objects.filter(competition=competition_id, miniature=request.POST.get('miniature_id')).delete()
                return JsonResponse({'status': 'success', 'miniature_id': request.POST.get('miniature_id')})
            else:
                return JsonResponse({'status': 'not_existing'})
        if 'miniature' in request.POST:
            if Competition.objects.get(id=competition_id).date_registration < datetime.now().astimezone():
                return JsonResponse({'error': "Cannot make changes to registration after registration deadline", 'status': 'reg_deadline'})
            form = MiniatureRegistrationForm(competition_id, data=request.POST)
            if form.is_valid():
                miniature_registration = form.save()
                return JsonResponse({'status': 'success', 'miniature_id': request.POST.get('miniature')})
            else:
                form_html = render_to_string('competitions/competition_registration_form.html', {'form': form}, request)
                return JsonResponse({'status': 'invalid_form', 'form': form_html})


class CompetitionPersonListView(View):

    def get(self, request, competition_id=None, *args, **kwargs):
        template_name = 'competitions/competition_competitors.html'

        if competition_id is None:
            return HttpResponseRedirect('/competitions')

        if not Competition.objects.filter(id=competition_id).exists():
            return HttpResponseRedirect('/competitions')

        registered_persons = {}
        registrations = MiniatureRegistration.objects.filter(competition=competition_id)

        for registration in registrations:
            if registered_persons.get(registration.miniature.owner.id) is None:
                registered_persons[registration.miniature.owner.id] = [registration.miniature.owner, []]
            registered_persons[registration.miniature.owner.id][1].append([
                registration.miniature,
                registration.additional_information,
                registration.category,
                registration.time_of_registration
            ])
        
        persons_and_miniatures = []

        for key, value in registered_persons.items():
            persons_and_miniatures.append(value)

        return render(request, template_name, {'persons_and_miniatures': persons_and_miniatures})

    def post(self, request, competition_id=None, *args, **kwargs):
        if not Competition.objects.filter(id=competition_id).exists():
            response = JsonResponse({'error': 'Competition does not exist'})
            response.status_code = 404
            return response
        if not request.user.is_superuser and not request.user == Competition.objects.get(id=competition_id).organizer:
            response = JsonResponse({'error': 'Denied access'})
            response.status_code = 403
            return response

        if request.POST.get('request') == 'unregister_miniature':
            if MiniatureRegistration.objects.filter(miniature=request.POST['miniature_id'], competition=competition_id).exists():
                owner = Miniature.objects.get(id=request.POST['miniature_id']).owner
                MiniatureRegistration.objects.filter(miniature=request.POST['miniature_id'], competition=competition_id).delete()
                if MiniatureRegistration.objects.filter(miniature__owner=owner.id).exists():
                    return JsonResponse({'status':'success', 'miniature_id': request.POST['miniature_id']})
                else:
                    return JsonResponse({'status':'all_miniatures', 'miniature_id': request.POST['miniature_id'], 'person_id': owner.id})
            else:
                return JsonResponse({'status': 'not_existing'})
        if request.POST.get('request') == 'unregister_person':
            is_person_present = False
            if MiniatureRegistration.objects.filter(miniature__owner=request.POST.get('person_id'), competition=competition_id).exists():
                MiniatureRegistration.objects.filter(miniature__owner=request.POST.get('person_id'), competition=competition_id).delete()
                return JsonResponse({'status': 'success', 'person_id': request.POST.get('person_id')})
            else:
                return JsonResponse({'status': 'not_existing'})
                

class CompetitionMiniatureCategoryView(View):

    def get(self, request, competition_id=None, *args, **kwargs):
        context = {}
        template_name = 'competitions/competition_miniature_category_list.html'

        if competition_id is None:
            return HttpResponseRedirect('/competitions')

        try:
            competition_model = Competition.objects.get(pk=competition_id)
        except Competition.DoesNotExist:
            return HttpResponseRedirect('/competitions')

        if not request.user.is_authenticated:
            return HttpResponseRedirect('/login?redirect_page=competition-create')

        if competition_model.organizer.id != request.user.id:
            return HttpResponseRedirect('/competition/{}'.format(competition_id))

        categories_and_count = []
        categories = CompetitionMiniatureCategory.objects.filter(competition=competition_id)
        for category in categories:
            categories_and_count.append([category, MiniatureRegistration.objects.filter(category=category.id, competition=competition_id).count()])

        context['competition_miniature_category'] = categories_and_count #CompetitionMiniatureCategory.objects.filter(competition=competition_id)
        context['competition_id'] = competition_id
        context['form'] = CompetitionMiniatureCategoryForm()

        return render(request, template_name, context)

    def post(self, request, competition_id=None, *args, **kwargs):
        template_name = 'competitions/competition_miniature_category_list.html'
        action = request.POST.get('action')

        if competition_id is None:
            return HttpResponseRedirect('/competitions')

        try:
            competition_model = Competition.objects.get(pk=competition_id)
        except Competition.DoesNotExist:
            return HttpResponseRedirect('/competitions')

        if not request.user.is_authenticated:
            return HttpResponseRedirect('/login?redirect_page=competition-create')

        if competition_model.organizer.id != request.user.id and not request.user.is_superuser:
            return HttpResponseRedirect('/competition/{}'.format(competition_id))

        if action == 'remove_category':
            if CompetitionMiniatureCategory.objects.filter(competition=competition_id, id=request.POST.get('id')).exists():
                CompetitionMiniatureCategory.objects.filter(competition=competition_id, id=request.POST.get('id')).delete()
                return JsonResponse({'status': 'success'})
            else:
                response = JsonResponse({'error': 'Miniature category does not exist'})
                response.status_code = 404
                return response
        if action == 'add_category':
            form = CompetitionMiniatureCategoryForm(data=request.POST)
            if form.is_valid():
                category = form.save()
                count = MiniatureRegistration.objects.filter(competition=competition_id, category=category.id).count()
                html = render_to_string('competitions/competition_category_row.html', {'category': category, 'category_count': count})
                return JsonResponse({'status': 'success', 'row': html})
            else:
                response = JsonResponse({'error': 'Invalid form'})
                response.status_code = 403
                return response


        data = request.POST.copy()
        if 'action' in data.keys():
            data.pop('action')
        data['competition'] = competition_id
        # if data['action'] == 'remove_category':
        #     try:
        #         competition_miniature_category = CompetitionMiniatureCategory.objects.get(pk=data['id'])
        #     except CompetitionMiniatureCategory.DoesNotExist:
        #         pass
        #         #TODO
        #     competition_miniature_category.delete()
        if action == 'update_category':
            try:
                competition_miniature_category = CompetitionMiniatureCategory.objects.get(pk=data['id'])
            except CompetitionMiniatureCategory.DoesNotExist:
                response = JsonResponse({'error': 'Miniature category does not exist'})
                response.status_code = 404
                return response
            form = CompetitionMiniatureCategoryForm(instance=competition_miniature_category, data=data)

        else:
            form = CompetitionMiniatureCategoryForm(data=data)

        if form.is_valid():
            comp_min_cat = form.save()
            if action == 'update_category':
                return JsonResponse(
                    {
                        'status': 'success',
                        'name': comp_min_cat.name,
                        'id': str(comp_min_cat.id),
                        'msg': 'Název se uložil.'
                    }
                )
            else:
                return HttpResponseRedirect('/competition/{}/categorys'.format(competition_id))
        else:
            return JsonResponse(
                {
                    'status': 'form_invalid',
                    'msg': 'Data se nepovedlo uložit.'
                }
            )
