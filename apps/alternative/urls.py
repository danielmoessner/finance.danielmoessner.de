from django.urls import path

from apps.alternative.views import form_views, views

app_name = 'alternative'

urlpatterns = [
    # FUNCTIONS
    # # reset-movies/
    path('reset-movies', views.reset_movies, name='reset_movies'),

    # depot
    path('add-depot/', form_views.AddDepotView.as_view(), name='add_depot'),
    path('edit-depot/<int:pk>/', form_views.EditDepotView.as_view(), name='edit_depot'),
    path('delete-depot/', form_views.DeleteDepotView.as_view(), name='delete_depot'),
    path('depot/<int:pk>/set-active', form_views.SetActiveDepotView.as_view(), name='set_depot'),

    # alternative
    path('add-alternative/', form_views.AddAlternativeView.as_view(), name='add_alternative'),
    path('edit-alternative/<slug:slug>/', form_views.EditAlternativeView.as_view(), name='edit_alternative'),
    path('delete-alternative/', form_views.DeleteAlternativeView.as_view(), name='delete_alternative'),

    # value
    path('add-value/', form_views.AddValueView.as_view(), name='add_value'),
    path('alternative/<slug:slug>/add-value/', form_views.AddValueAlternativeView.as_view(), name='add_value'),
    path('alternative/<slug:slug>/edit-value/<int:pk>/', form_views.EditValueView.as_view(), name='edit_value'),
    path('alternative/<slug:slug>/delete-value/<int:pk>/', form_views.DeleteValueView.as_view(), name='delete_value'),

    # flow
    path('add-flow/', form_views.AddFlowView.as_view(), name='add_flow'),
    path('alternative/<slug:slug>/add-flow/', form_views.AddFlowAlternativeView.as_view(), name='add_flow'),
    path('alternative/<slug:slug>/edit-flow/<int:pk>/', form_views.EditFlowView.as_view(), name='edit_flow'),
    path('alternative/<slug:slug>/delete-flow/<int:pk>/', form_views.DeleteFlowView.as_view(), name='delete_flow'),

    # timespan
    path('add-timespan/', form_views.AddTimespanView.as_view(), name='add_timespan'),
    path('delete-timespan/<int:pk>/', form_views.DeleteTimespanView.as_view(), name='delete_timespan'),
    path('set-timespan/<int:pk>/', form_views.SetActiveTimespanView.as_view(), name='set_timespan'),

    # PAGES
    path('depot/<int:pk>/', (views.IndexView.as_view()), name='index'),
    path('alternative/<int:pk>/', (views.AlternativeView.as_view()), name='alternative'),
]
