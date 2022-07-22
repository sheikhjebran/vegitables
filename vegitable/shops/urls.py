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
    path('edit_arrival_entry/<int:arrival_id>/', views.modify_arrival, name='modify_arrival'),

    #Misc Entry URL
    path('misc_entry', views.misc_entry, name='misc_entry'),
    path('misc/prev/<int:page_number>/',views.misc_prev_page, name="misc_prev_page"),
    path('misc/next/<int:page_number>/',views.misc_next_page, name="misc_next_page"),
    path('add_misc_entry', views.add_new_misc_entry, name='add_new_misc_entry'),
    path('add_misc', views.add_misc_entry, name='add_misc_entry'),
    path('edit_misc_entry/<int:misc_id>/', views.edit_misc_entry, name='edit_misc_entry'),
    path('misc_total_iframe', views.total_amount_misc_entry, name='total_amount_misc_entry'),
    
    #Sales Entry URL
    path('sales_bill_entry', views.sales_bill_entry, name='sales_bill_entry'),
    path('sales_bill/prev/<int:page_number>/',views.sales_bill_prev_page, name="sales_bill_prev_page"),
    path('sales_bill/next/<int:page_number>/',views.sales_bill_next_page, name="sales_bill_next_page"),
    path('add_sales_bill_entry', views.add_new_sales_bill_entry, name='add_new_sales_bill_entry'),
]