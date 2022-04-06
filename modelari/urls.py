from django.contrib.auth.views import PasswordChangeView
from django.urls import path, include
from django.conf import settings
from .views import HomePageView, LoginPageView, PersonView, RegistrationPageView, LogoutPageView, AccountView, \
    UsersView, CompetitionCreateView, CompetitionDetailView, CategoriesView, CompetitionOverviewView, \
    CompetitionPersonListView, CompetitionRegistrationView, PersonMiniaturesView, CompetitionMiniatureCategoryView
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('', HomePageView.as_view()),
    path('login/', LoginPageView.as_view()),
    path('registration/', RegistrationPageView.as_view()),
    path('logout/', LogoutPageView.as_view()),
    path('account/', AccountView.as_view()),
    path('persons/', PersonView.as_view(), name="persons"),
    path('persons/<int:person_id>', PersonMiniaturesView.as_view(), name="persons"),
    path('users/', UsersView.as_view()),
    path('competition/create', CompetitionCreateView.as_view(), name="competition_create"),
    path('competition/<int:competition_id>', CompetitionDetailView.as_view(), name="competition_detail"),
    path('competition/<int:competition_id>/registration', CompetitionRegistrationView.as_view(), name="competition_detail"),
    path('success/', TemplateView.as_view(template_name="succes.html")),
    path('categories/', CategoriesView.as_view(), name='categories'),
    path('competitions/', CompetitionOverviewView.as_view(), name='competitions'),
    path('competition/<int:competition_id>/persons', CompetitionPersonListView.as_view(), name="competition_detail"),
    path('competition/<int:competition_id>/categorys', CompetitionMiniatureCategoryView.as_view(), name="competition_categorys"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
