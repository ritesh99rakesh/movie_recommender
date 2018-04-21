from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.template import loader
from django.http import HttpResponse
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView, FormView
from django.http import HttpResponseRedirect
from ..decorators import student_required

from ..decorators import student_required
from ..forms import StudentInterestsForm, StudentSignUpForm, TakeQuizForm, Movie_name
from ..models import Quiz, Student, TakenQuiz, User


import subprocess, shlex

movie_name = ""
no_of_movie = 0

def dashboard(request):
    print("You are a student!!")
    template = loader.get_template('classroom/dashboard.html')
    context = {
        'company_name': 'AcadAI',
    }
    return HttpResponse(template.render(context, request))


class StudentSignUpView(CreateView):
    model = User
    form_class = StudentSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'student'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('students:quiz_list')



# @method_decorator([login_required, student_required], name='dispatch')
# class MovieParameter(FormView):
#     print('into movie_parameter')
#     template_name = 'classroom/movie_parameter.html'
#     form_class = Movie_name

#     def get_success_url(self):
#         print('get_success_url')
#         return ('students:recommend') #might have to change this

#     def form_valid(self, form):
#         print('into form valid')
#         print(form.cleaned_data)
#         if form.is_valid():
#             print("form is valid")
#             print(form.cleaned_data)
#             print("Name of the movie: ", form.cleaned_data['movie_name'])
#             print("Type of movie_name: ", type(form.cleaned_data['movie_name']))
#             global movie_name
#             movie_name = form.cleaned_data['movie_name']
#             return HttpResponseRedirect(reverse(self.get_success_url()))


@login_required
@student_required
def MovieParameter(request):
    print("into movie parameter")
    global movie_name, no_of_movie
    subprocess.call('pwd')
    if request.method == 'POST':
        print('into POST')
        form = Movie_name(request.POST)
        if form.is_valid():
            print('form is valid')
            print(form.cleaned_data['movie_name'])
            movie_name = form.cleaned_data['movie_name']
            no_of_movie = form.cleaned_data['no_of_movie']
            print('movie_name: ', movie_name)
            context = {'form': form}
            return HttpResponseRedirect(reverse('students:recommend'))
    else:
        print('into else')
        form = Movie_name()

    return render(request, 'classroom/movie_parameter.html', {'form': form})

@login_required
@student_required
def recommend(request):
    template = loader.get_template('classroom/recommend.html')
    subprocess.call(shlex.split('pwd'))
    global movie_name, no_of_movie
    print('into recommend************************************')
    print('movie_name: ', movie_name)
    print('calling function############################################')
    subprocess.call(shlex.split("python main.py " + str(movie_name)))
    print('function over')
    movies = open('movies.txt', 'r').read().split(',')[0:no_of_movie]
    context={'movie_array': movies, 'no_of_movie': no_of_movie}
    print(movies)
    return HttpResponse(template.render(context, request))


@method_decorator([login_required, student_required], name='dispatch')
class StudentInterestsView(UpdateView):
    model = Student
    form_class = StudentInterestsForm
    template_name = 'classroom/students/interests_form.html'
    success_url = reverse_lazy('students:quiz_list')

    def get_object(self):
        return self.request.user.student

    def form_valid(self, form):
        messages.success(self.request, 'Interests updated with success!')
        return super().form_valid(form)


@method_decorator([login_required, student_required], name='dispatch')
class QuizListView(ListView):
    model = Quiz
    ordering = ('name', )
    context_object_name = 'quizzes'
    template_name = 'classroom/students/quiz_list.html'

    def get_queryset(self):
        student = self.request.user.student
        student_interests = student.interests.values_list('pk', flat=True)
        taken_quizzes = student.quizzes.values_list('pk', flat=True)
        queryset = Quiz.objects.filter(subject__in=student_interests) \
            .exclude(pk__in=taken_quizzes) \
            .annotate(questions_count=Count('questions')) \
            .filter(questions_count__gt=0)
        return queryset


@method_decorator([login_required, student_required], name='dispatch')
class TakenQuizListView(ListView):
    model = TakenQuiz
    context_object_name = 'taken_quizzes'
    template_name = 'classroom/students/taken_quiz_list.html'

    def get_queryset(self):
        queryset = self.request.user.student.taken_quizzes \
            .select_related('quiz', 'quiz__subject') \
            .order_by('quiz__name')
        return queryset


@login_required
@student_required
def take_quiz(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    student = request.user.student

    if student.quizzes.filter(pk=pk).exists():
        return render(request, 'students/taken_quiz.html')

    total_questions = quiz.questions.count()
    unanswered_questions = student.get_unanswered_questions(quiz)
    total_unanswered_questions = unanswered_questions.count()
    progress = 100 - round(((total_unanswered_questions - 1) / total_questions) * 100)
    question = unanswered_questions.first()

    if request.method == 'POST':
        form = TakeQuizForm(question=question, data=request.POST)
        if form.is_valid():
            with transaction.atomic():
                student_answer = form.save(commit=False)
                student_answer.student = student
                student_answer.save()
                if student.get_unanswered_questions(quiz).exists():
                    return redirect('students:take_quiz', pk)
                else:
                    correct_answers = student.quiz_answers.filter(answer__question__quiz=quiz, answer__is_correct=True).count()
                    score = round((correct_answers / total_questions) * 100.0, 2)
                    TakenQuiz.objects.create(student=student, quiz=quiz, score=score)
                    if score < 50.0:
                        messages.warning(request, 'Better luck next time! Your score for the quiz %s was %s.' % (quiz.name, score))
                    else:
                        messages.success(request, 'Congratulations! You completed the quiz %s with success! You scored %s points.' % (quiz.name, score))
                    return redirect('students:quiz_list')
    else:
        form = TakeQuizForm(question=question)

    return render(request, 'classroom/students/take_quiz_form.html', {
        'quiz': quiz,
        'question': question,
        'form': form,
        'progress': progress
    })
