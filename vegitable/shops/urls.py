from django.urls import path

from . import views

urlpatterns = [
    # webpage URL
    path('', views.index, name="index"),

    # Dashboard Authentication
    path('authenticate', views.get_authenticate, name="get_authenticate"),
    path('logout', views.logout, name="logout"),

    # dashboard URL
    path('home', views.home, name='home'),
    path('home/prev/<int:page_number>/',views.home_prev_page, name="home_prev_page"),
    path('home/next/<int:page_number>/',views.home_next_page, name="home_next_page"),

    # Arrival Entry URL
    path('add_arrival_entry', views.add_new_arrival_entry, name='add_new_arrival_entry'),
    path('add_arrival', views.add_arrival, name='add_arrival'),

    #Misc Entry URL
    path('misc_entry', views.misc_entry, name='misc_entry'),
    path('misc/prev/<int:page_number>/',views.misc_prev_page, name="misc_prev_page"),
    path('misc/next/<int:page_number>/',views.misc_next_page, name="misc_next_page"),
    path('add_misc_entry', views.add_new_misc_entry, name='add_new_misc_entry'),
    path('add_misc', views.add_misc_entry, name='add_misc_entry'),

]