from django.shortcuts import render

# Home page
def inherited_form(request):
    return render(request, 'HTMLs/inherited_form.html')
