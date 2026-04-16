from django.urls import path
from . import views
from .views import chat_view, chatbot_query ,crawl_and_embed_view, log_clicked_url, save_user_info

urlpatterns = [
    path("", views.chat_view, name="chat"),
    path("chat/", views.chatbot_query, name="chatbot_query"),
    path('crawl/', views.crawl_and_embed_view, name='crawl_and_embed'),
    path("chat/get-user-name/", views.get_user_name, name="get_user_name"), # for getting user name to display on bot
    path("log-click/", views.log_clicked_url, name="log_clicked_url"),  # for logging of clickedURL
    path("chat/save-user-info/", views.save_user_info, name="save_user_info"), # for saving user info from form on chatbot
]
