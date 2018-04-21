from django.urls import include, path

from .views import classroom, students

urlpatterns = [
    path('', classroom.home, name='home'),

    path('students/', include(([
        path('', students.dashboard, name='dashboard'),
        path('recommend/', students.recommend, name='recommend'),
        path('movie_parameter/', students.MovieParameter, name='MovieParameter'),
        path('interests/', students.StudentInterestsView.as_view(), name='student_interests'),
        path('taken/', students.TakenQuizListView.as_view(), name='taken_quiz_list'),
        path('quiz/<int:pk>/', students.take_quiz, name='take_quiz'),
    ], 'classroom'), namespace='students')),
]
